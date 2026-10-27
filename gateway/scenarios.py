"""
ThreatLens Repeatable Gateway Test Scenarios (Phase 2).

Provides five deterministic, repeatable test scenarios:
1. benign_charging: Full legitimate charging sequence (100% ALLOW).
2. excessive_current: CSMS pushes 180A setpoint (> 100A safe cap) -> CLAMP to 100.0A.
3. command_flooding: Rapid setpoint changes (< 1.0s interval) -> Rule R-02 BLOCK.
4. unauthorized_command: Rogue remote start injection -> Rule R-03 SecurityError BLOCK.
5. malformed_message: Protocol syntax / framing violation -> FormationViolation BLOCK.
"""

import asyncio
import copy
from dataclasses import dataclass, field
import json
import logging
import time
from typing import Any, Dict, List, Optional

from gateway.config import GatewayConfig
from gateway.mock.mock_charger import MockChargePoint
from gateway.mock.mock_csms import MockCSMS
from gateway.models import (
    OCPPCall,
    OCPPCallError,
    OCPPCallResult,
    OCPPErrorCode,
    OCPPFrameParser,
    create_call,
)
from gateway.policy import GatewayPolicyEngine, PolicyConfig, PolicyDecision
from gateway.proxy import GatewayProxy

logger = logging.getLogger("ThreatLens.Gateway.Scenarios")


@dataclass
class ScenarioInfo:
    """Metadata describing a test scenario."""
    id: str
    name: str
    category: str
    description: str
    expected_decisions: List[str]  # e.g. ["ALLOW", "CLAMP", "BLOCK"]
    threat_actor: str
    mitigation_rule: str


SCENARIO_CATALOG: Dict[str, ScenarioInfo] = {
    "benign_charging": ScenarioInfo(
        id="benign_charging",
        name="Benign Normal Charging Sequence",
        category="Baseline",
        description="Standard EV charging workflow (Boot -> Status -> RemoteStart -> SetProfile -> RemoteStop).",
        expected_decisions=["ALLOW"],
        threat_actor="Authorized CSMS & Driver",
        mitigation_rule="R-00 (Pass-Through)",
    ),
    "excessive_current": ScenarioInfo(
        id="excessive_current",
        name="Overcurrent Setpoint Attack",
        category="Safety Violation",
        description="CSMS requests 180A setpoint exceeding the 100A safe ceiling and 150A hardware breaker.",
        expected_decisions=["CLAMP"],
        threat_actor="Compromised CSMS / Operator Misconfig",
        mitigation_rule="R-01 (Hardware Current Ceiling)",
    ),
    "command_flooding": ScenarioInfo(
        id="command_flooding",
        name="Command Flooding / Flutter Attack",
        category="Denial of Service",
        description="CSMS floods 3 rapid SetChargingProfile updates within 0.5s interval to stress hardware.",
        expected_decisions=["ALLOW", "BLOCK"],
        threat_actor="Malicious Actor / Botnet Flooding",
        mitigation_rule="R-02 (Rate Limiting Protection)",
    ),
    "unauthorized_command": ScenarioInfo(
        id="unauthorized_command",
        name="Unauthorized Start Injection",
        category="Authentication Bypass",
        description="Rogue CSMS injects RemoteStartTransaction with spoofed or unauthorized token.",
        expected_decisions=["BLOCK"],
        threat_actor="Network Intruder / Man-In-The-Middle",
        mitigation_rule="R-03 (State Machine & Auth Validation)",
    ),
    "malformed_message": ScenarioInfo(
        id="malformed_message",
        name="Malformed OCPP Frame Injection",
        category="Protocol Fuzzing",
        description="Injects syntactically illegal non-dict payload to probe parser vulnerabilities.",
        expected_decisions=["BLOCK"],
        threat_actor="Protocol Fuzzer / Exploiter",
        mitigation_rule="OCPP 1.6-J Framing Validation",
    ),
}


@dataclass
class ScenarioExecutionResult:
    """Execution outcome of an automated scenario run."""
    scenario_id: str
    scenario_name: str
    status: str  # "SUCCESS" or "FAILED"
    total_messages: int
    decisions: List[Dict[str, Any]]
    charger_received_limit: Optional[float]
    summary: str
    verification_passed: bool
    execution_time_seconds: float


class ScenarioRunner:
    """
    Executes mock scenarios against a running GatewayProxy instance
    or sets up a dedicated testbench session.
    """

    def __init__(
        self,
        proxy: Optional[GatewayProxy] = None,
        csms: Optional[MockCSMS] = None,
    ):
        self.proxy = proxy
        self.csms = csms

    async def run(
        self,
        scenario_id: str,
        charger_id: str = "CP_DEMO_01",
        config: Optional[GatewayConfig] = None,
    ) -> ScenarioExecutionResult:
        """Execute one of the 5 reproducible test scenarios."""
        start_time = time.time()
        recorded_decisions: List[Dict[str, Any]] = []

        cfg = config or (self.proxy.config if self.proxy else GatewayConfig())
        # Record audit decisions in local list
        def _capture_audit(evt):
            recorded_decisions.append(evt)

        # Standalone proxy setup if not injected
        local_proxy = None
        if not self.proxy:
            local_proxy = GatewayProxy(cfg, audit_callback=_capture_audit)
            await local_proxy.start()
            active_proxy = local_proxy
        else:
            active_proxy = self.proxy
            # Chain audit callback
            original_cb = active_proxy.audit_callback
            def _chained_cb(evt):
                _capture_audit(evt)
                if original_cb:
                    original_cb(evt)
            active_proxy.audit_callback = _chained_cb

        # Reuse existing running mock CSMS or spin up a local mock CSMS on csms_port
        local_csms = None
        if self.csms and self.csms.is_running:
            mock_csms = self.csms
            mock_csms.reset_history()
        else:
            local_csms = MockCSMS(host=cfg.csms_host, port=cfg.csms_port)
            await local_csms.start()
            mock_csms = local_csms

        # Spin up local mock Charger
        mock_charger = MockChargePoint(
            charge_point_id=charger_id,
            gateway_host=cfg.host,
            gateway_port=cfg.charger_port,
        )

        try:
            # Charger connects to Gateway
            await mock_charger.connect(timeout=4.0)
            # Wait for mock CSMS to see connection
            await mock_csms.wait_for_connection(charger_id, timeout=4.0)

            # Route to scenario implementation
            if scenario_id == "benign_charging":
                passed, summary = await self._exec_benign_charging(mock_charger, mock_csms, charger_id)
            elif scenario_id == "excessive_current":
                passed, summary = await self._exec_excessive_current(mock_charger, mock_csms, charger_id)
            elif scenario_id == "command_flooding":
                passed, summary = await self._exec_command_flooding(mock_charger, mock_csms, charger_id)
            elif scenario_id == "unauthorized_command":
                passed, summary = await self._exec_unauthorized_command(mock_charger, mock_csms, charger_id)
            elif scenario_id == "malformed_message":
                passed, summary = await self._exec_malformed_message(mock_charger, mock_csms, charger_id)
            else:
                passed = False
                summary = f"Unknown scenario id '{scenario_id}'"

            elapsed = time.time() - start_time
            info = SCENARIO_CATALOG.get(scenario_id, ScenarioInfo(scenario_id, scenario_id, "", "", [], "", ""))

            return ScenarioExecutionResult(
                scenario_id=scenario_id,
                scenario_name=info.name,
                status="SUCCESS" if passed else "FAILED",
                total_messages=len(recorded_decisions),
                decisions=recorded_decisions,
                charger_received_limit=mock_charger.active_limit,
                summary=summary,
                verification_passed=passed,
                execution_time_seconds=round(elapsed, 3),
            )

        finally:
            await mock_charger.disconnect()
            if local_csms:
                await local_csms.stop()
            if local_proxy:
                await local_proxy.stop()

    async def _exec_benign_charging(
        self,
        charger: MockChargePoint,
        csms: MockCSMS,
        cp_id: str,
    ) -> tuple[bool, str]:
        """Execute benign charging workflow."""
        # 1. Charger Boot
        await charger.send_boot_notification()
        # 2. Charger Status
        await charger.send_status_notification("Available")
        # 3. CSMS starts transaction with valid token
        res_start = await csms.send_call(cp_id, "RemoteStartTransaction", {"idTag": "VALID_CARD_123", "connectorId": 1})
        # 4. Charger sends telemetry
        await charger.send_meter_values(current_a=80.0)
        # 5. CSMS adjusts charging limit to 90A (within safe 100A cap)
        await asyncio.sleep(0.05)
        res_profile = await csms.send_call(cp_id, "SetChargingProfile", {"limit": 90.0})
        # 6. CSMS stops transaction
        await csms.send_call(cp_id, "RemoteStopTransaction", {"transactionId": 1001})

        passed = (
            charger.active_limit == 90.0
            and isinstance(res_start, OCPPCallResult)
            and isinstance(res_profile, OCPPCallResult)
        )
        summary = (
            "Benign session completed: BootNotification, StatusNotification, RemoteStart, "
            f"SetChargingProfile (90A), and RemoteStop were all evaluated as ALLOW. Active limit: {charger.active_limit}A."
        )
        return passed, summary

    async def _exec_excessive_current(
        self,
        charger: MockChargePoint,
        csms: MockCSMS,
        cp_id: str,
    ) -> tuple[bool, str]:
        """Execute excessive current injection (180A -> clamped to 100A)."""
        await charger.send_boot_notification()
        await charger.send_status_notification("Charging")

        # Attack: CSMS issues 180A setpoint
        res = await csms.send_call(cp_id, "SetChargingProfile", {"limit": 180.0})

        # Charger should receive 100.0A (clamped), not 180.0A
        passed = charger.active_limit == 100.0
        summary = (
            f"Overcurrent manipulation detected: Requested 180.0A was intercepted and clamped "
            f"to safe hardware cap 100.0A. Charger received setpoint {charger.active_limit}A."
        )
        return passed, summary

    async def _exec_command_flooding(
        self,
        charger: MockChargePoint,
        csms: MockCSMS,
        cp_id: str,
    ) -> tuple[bool, str]:
        """Execute rapid command flooding (< 5.0s interval)."""
        await charger.send_boot_notification()

        # Send 1st command
        res1 = await csms.send_call(cp_id, "SetChargingProfile", {"limit": 80.0})

        # Flood 2nd command immediately (0.05s later)
        await asyncio.sleep(0.05)
        res2 = await csms.send_call(cp_id, "SetChargingProfile", {"limit": 85.0})

        # Flood 3rd command immediately
        await asyncio.sleep(0.05)
        res3 = await csms.send_call(cp_id, "SetChargingProfile", {"limit": 90.0})

        passed = (
            isinstance(res1, OCPPCallResult)
            and isinstance(res2, OCPPCallError)
            and isinstance(res3, OCPPCallError)
        )
        summary = (
            "Command flutter attack intercepted: First command allowed (80A), "
            f"subsequent commands blocked by Rule R-02 rate limiting. Charger limit retained at {charger.active_limit}A."
        )
        return passed, summary

    async def _exec_unauthorized_command(
        self,
        charger: MockChargePoint,
        csms: MockCSMS,
        cp_id: str,
    ) -> tuple[bool, str]:
        """Execute rogue remote start transaction injection."""
        await charger.send_boot_notification()
        charger.status = "Available"

        # Inject unauthorized token
        res = await csms.send_call(
            cp_id,
            "RemoteStartTransaction",
            {"idTag": "ROGUE_UNAUTHORIZED_TOKEN", "connectorId": 1},
        )

        passed = isinstance(res, OCPPCallError) and res.error_code == "SecurityError"
        summary = (
            f"Unauthorized start blocked: Rogue token 'ROGUE_UNAUTHORIZED_TOKEN' was rejected "
            f"with SecurityError by Rule R-03. Charger remained in status '{charger.status}'."
        )
        return passed, summary

    async def _exec_malformed_message(
        self,
        charger: MockChargePoint,
        csms: MockCSMS,
        cp_id: str,
    ) -> tuple[bool, str]:
        """Execute malformed frame injection."""
        # Send raw bad frame from charger
        # Bad CALL: payload is integer instead of dict
        bad_frame = json.dumps([2, "malf-001", "Heartbeat", 12345])
        await charger.send_raw(bad_frame)

        # Wait briefly for reply
        await asyncio.sleep(0.1)

        # Charger should have received CALLERROR FormationViolation
        errors = [e for e in charger.received_errors if e.unique_id == "malf-001"]
        passed = len(errors) > 0 and errors[0].error_code == "FormationViolation"
        summary = (
            "Malformed message rejected: Payload type violation triggered "
            "OCPP CALLERROR 'FormationViolation'. Frame was not forwarded."
        )
        return passed, summary
