"""
ThreatLens Gateway Policy Engine Tests (Phase 1).

Tests deterministic ALLOW, CLAMP, and BLOCK safety rules:
- Rule R-01: Hardware current ceiling & overcurrent clamping
- Rule R-02: Command rate limiting (< 5.0s interval)
- Rule R-03: Authorization validation & rogue token rejection
- Rule R-04: Thermal lockout (>= 45.0°C)
- Integration through GatewayProxy
"""

import asyncio
import json
import time
import pytest
from websockets.asyncio.client import connect
from websockets.asyncio.server import serve
from websockets.typing import Subprotocol

from gateway.config import GatewayConfig
from gateway.models import (
    OCPPCall,
    OCPPCallError,
    OCPPCallResult,
    OCPPErrorCode,
    OCPPFrameParser,
    create_call,
    create_call_result,
)
from gateway.policy import (
    GatewayPolicyEngine,
    PolicyConfig,
    PolicyDecision,
)
from gateway.proxy import GatewayProxy


# =========================================================================
# Unit Tests: Policy Engine Logic
# =========================================================================

def test_policy_allow_benign_commands():
    """Verify standard benign operations receive ALLOW."""
    engine = GatewayPolicyEngine()

    # Charger -> CSMS BootNotification
    call1 = create_call("BootNotification", {"chargePointModel": "EV-100", "chargePointVendor": "ThreatLens"})
    res1 = engine.evaluate_call(call1, direction="CHARGER_TO_CSMS", charge_point_id="CP_01")
    assert res1.decision == PolicyDecision.ALLOW
    assert res1.rule_id == "R-00"

    # CSMS -> Charger Heartbeat / TriggerMessage
    call2 = create_call("TriggerMessage", {"requestedMessage": "StatusNotification"})
    res2 = engine.evaluate_call(call2, direction="CSMS_TO_CHARGER", charge_point_id="CP_01")
    assert res2.decision == PolicyDecision.ALLOW


def test_rule_r01_overcurrent_clamping():
    """Verify Rule R-01 clamps current setpoints exceeding configured cap."""
    config = PolicyConfig(current_cap_enabled=True, current_cap_value=100.0, hardware_max_current=150.0)
    engine = GatewayPolicyEngine(config)

    # 1. Test canonical OCPP 1.6-J payload with 180A requested limit
    canonical_payload = {
        "connectorId": 1,
        "csChargingProfiles": {
            "chargingProfileId": 1,
            "stackLevel": 0,
            "chargingProfilePurpose": "TxDefaultProfile",
            "chargingProfileKind": "Absolute",
            "chargingSchedule": {
                "chargingRateUnit": "A",
                "chargingSchedulePeriod": [{"startPeriod": 0, "limit": 180.0, "numberPhases": 3}],
            },
        },
    }
    call = create_call("SetChargingProfile", canonical_payload)
    res = engine.evaluate_call(call, direction="CSMS_TO_CHARGER", charge_point_id="CP_01")

    assert res.decision == PolicyDecision.CLAMP
    assert res.rule_id == "R-01"
    assert res.original_limit == 180.0
    assert res.modified_limit == 100.0
    assert res.modified_payload is not None
    # Check that modified payload has limit clamped to 100.0
    clamped_periods = res.modified_payload["csChargingProfiles"]["chargingSchedule"]["chargingSchedulePeriod"]
    assert clamped_periods[0]["limit"] == 100.0

    # 2. Test safe limit (80A) passes through with ALLOW
    safe_payload = {"limit": 80.0}
    safe_call = create_call("SetChargingProfile", safe_payload)
    safe_res = engine.evaluate_call(safe_call, direction="CSMS_TO_CHARGER", charge_point_id="CP_01", now=time.time() + 10.0)
    assert safe_res.decision == PolicyDecision.ALLOW


def test_rule_r02_command_rate_limiting():
    """Verify Rule R-02 blocks commands arriving faster than min_interval_seconds."""
    config = PolicyConfig(rate_limiting_enabled=True, min_command_interval_seconds=5.0)
    engine = GatewayPolicyEngine(config)

    t0 = 1000.0
    call1 = create_call("SetChargingProfile", {"limit": 80.0})
    res1 = engine.evaluate_call(call1, direction="CSMS_TO_CHARGER", charge_point_id="CP_01", now=t0)
    assert res1.decision == PolicyDecision.ALLOW

    # Rapid second command 1.5s later (violates 5.0s min interval)
    call2 = create_call("SetChargingProfile", {"limit": 85.0})
    res2 = engine.evaluate_call(call2, direction="CSMS_TO_CHARGER", charge_point_id="CP_01", now=t0 + 1.5)
    assert res2.decision == PolicyDecision.BLOCK
    assert res2.rule_id == "R-02"
    assert "rate limit exceeded" in res2.reason.lower()

    # Third command 6.0s after initial command (now allowed)
    call3 = create_call("SetChargingProfile", {"limit": 90.0})
    res3 = engine.evaluate_call(call3, direction="CSMS_TO_CHARGER", charge_point_id="CP_01", now=t0 + 6.0)
    assert res3.decision == PolicyDecision.ALLOW


def test_rule_r03_authorization_validation():
    """Verify Rule R-03 blocks rogue/unauthorized transaction starts."""
    config = PolicyConfig(auth_validation_enabled=True)
    engine = GatewayPolicyEngine(config)

    # Rogue token
    bad_call = create_call("RemoteStartTransaction", {"idTag": "ROGUE_INJECTED_TOKEN", "connectorId": 1})
    res_bad = engine.evaluate_call(bad_call, direction="CSMS_TO_CHARGER", charge_point_id="CP_01")
    assert res_bad.decision == PolicyDecision.BLOCK
    assert res_bad.rule_id == "R-03"
    assert res_bad.error_code == OCPPErrorCode.SecurityError

    # Legitimate token
    good_call = create_call("RemoteStartTransaction", {"idTag": "VALID_RFID_USER", "connectorId": 1})
    res_good = engine.evaluate_call(good_call, direction="CSMS_TO_CHARGER", charge_point_id="CP_01")
    assert res_good.decision == PolicyDecision.ALLOW


def test_rule_r04_thermal_lockout():
    """Verify Rule R-04 blocks new transactions or setpoints when temperature exceeds threshold."""
    config = PolicyConfig(thermal_lockout_enabled=True, thermal_lockout_threshold_c=45.0)
    engine = GatewayPolicyEngine(config)

    # Normal temperature (30°C) -> ALLOW
    engine.set_charger_temperature("CP_01", 30.0)
    call1 = create_call("RemoteStartTransaction", {"idTag": "VALID_TAG", "connectorId": 1})
    res1 = engine.evaluate_call(call1, direction="CSMS_TO_CHARGER", charge_point_id="CP_01")
    assert res1.decision == PolicyDecision.ALLOW

    # Overheated temperature (48°C) -> BLOCK
    engine.set_charger_temperature("CP_01", 48.0)
    call2 = create_call("RemoteStartTransaction", {"idTag": "VALID_TAG", "connectorId": 1})
    res2 = engine.evaluate_call(call2, direction="CSMS_TO_CHARGER", charge_point_id="CP_01")
    assert res2.decision == PolicyDecision.BLOCK
    assert res2.rule_id == "R-04"
    assert "thermal lockout" in res2.reason.lower()


# =========================================================================
# Integration Tests: Policy Enforcement in GatewayProxy
# =========================================================================

def test_proxy_enforces_clamping_on_wire():
    """
    Integration test: CSMS sends 180A SetChargingProfile to Charger via GatewayProxy.
    Gateway clamps limit to 100A; Charger receives modified frame with limit=100.0.
    """
    async def _run():
        charger_received = []
        audit_events = []
        csms_connections = []

        # 1. Mock CSMS on 9301
        async def mock_csms_handler(ws):
            csms_connections.append(ws)
            async for msg in ws:
                pass

        csms_server = await serve(mock_csms_handler, host="127.0.0.1", port=9301, subprotocols=[Subprotocol("ocpp1.6")])

        # 2. Start Gateway on 9300 -> 9301 with cap=100A
        config = GatewayConfig(charger_port=9300, csms_port=9301)
        config.policy.current_cap_enabled = True
        config.policy.current_cap_value = 100.0

        proxy = GatewayProxy(config, audit_callback=lambda evt: audit_events.append(evt))
        await proxy.start()

        try:
            # 3. Charger connects to Gateway at 9300
            async with connect("ws://127.0.0.1:9300/CP_CLAMP_TEST", subprotocols=[Subprotocol("ocpp1.6")]) as charger_ws:
                # Wait briefly for CSMS connection to be accepted by mock CSMS server
                for _ in range(50):
                    if csms_connections:
                        break
                    await asyncio.sleep(0.02)

                csms_ws = csms_connections[0]
                call = create_call("SetChargingProfile", {"limit": 180.0}, unique_id="clamp-req-1")

                # CSMS pushes 180A SetChargingProfile downstream
                await csms_ws.send(call.to_json())

                # Charger receives the CLAMPED call (100A)
                msg = await asyncio.wait_for(charger_ws.recv(), timeout=2.0)
                charger_received.append(msg)

                frame = OCPPFrameParser.parse_raw(msg)
                assert isinstance(frame, OCPPCall)
                assert frame.unique_id == "clamp-req-1"
                assert frame.payload["limit"] == 100.0  # Successfully clamped from 180.0 to 100.0!

                # Check audit event
                assert len(audit_events) == 1
                assert audit_events[0]["decision"] == "CLAMP"
                assert audit_events[0]["rule_id"] == "R-01"
                assert audit_events[0]["original_limit"] == 180.0
                assert audit_events[0]["modified_limit"] == 100.0

        finally:
            await proxy.stop()
            csms_server.close()
            await csms_server.wait_closed()

    asyncio.run(_run())


def test_proxy_enforces_blocking_on_wire():
    """
    Integration test: CSMS sends unauthorized RemoteStartTransaction.
    Gateway returns CALLERROR: SecurityError back to CSMS; Charger receives nothing.
    """
    async def _run():
        csms_connections = []
        csms_received = []
        audit_events = []

        # 1. Mock CSMS on 9311
        async def mock_csms_handler(ws):
            csms_connections.append(ws)
            async for msg in ws:
                csms_received.append(msg)

        csms_server = await serve(mock_csms_handler, host="127.0.0.1", port=9311, subprotocols=[Subprotocol("ocpp1.6")])

        # 2. Start Gateway on 9310 -> 9311
        config = GatewayConfig(charger_port=9310, csms_port=9311)
        proxy = GatewayProxy(config, audit_callback=lambda evt: audit_events.append(evt))
        await proxy.start()

        try:
            # 3. Charger connects to Gateway at 9310
            async with connect("ws://127.0.0.1:9310/CP_BLOCK_TEST", subprotocols=[Subprotocol("ocpp1.6")]) as charger_ws:
                for _ in range(50):
                    if csms_connections:
                        break
                    await asyncio.sleep(0.02)

                csms_ws = csms_connections[0]
                call = create_call("RemoteStartTransaction", {"idTag": "ROGUE_ATTACKER_ID"}, unique_id="block-req-1")

                # Send call from CSMS towards Charger
                await csms_ws.send(call.to_json())

                # CSMS receives synthesized CALLERROR back from Gateway in mock_csms_handler
                for _ in range(50):
                    if csms_received:
                        break
                    await asyncio.sleep(0.02)

                assert len(csms_received) == 1
                reply_frame = OCPPFrameParser.parse_raw(csms_received[0])

                assert isinstance(reply_frame, OCPPCallError)
                assert reply_frame.unique_id == "block-req-1"
                assert reply_frame.error_code == "SecurityError"

                # Check that charger received zero messages
                with pytest.raises(asyncio.TimeoutError):
                    await asyncio.wait_for(charger_ws.recv(), timeout=0.3)

                # Check audit event
                assert len(audit_events) == 1
                assert audit_events[0]["decision"] == "BLOCK"
                assert audit_events[0]["rule_id"] == "R-03"

        finally:
            await proxy.stop()
            csms_server.close()
            await csms_server.wait_closed()

    asyncio.run(_run())
