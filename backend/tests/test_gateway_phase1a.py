"""
ThreatLens Gateway Phase 1A Verification Test Suite.

Tests OCPP 1.6-J frame parsing, structural validation, RPC error semantics,
request-response correlation, monotonic sequence tokens, max frame sizes,
asymmetric error handling, and async WebSocket proxy pass-through.
"""

import asyncio
import json
import time
import pytest
import websockets
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
    OCPPMessageType,
    OCPPParseError,
    RequestTracker,
    create_call,
    create_call_error,
    create_call_result,
)
from gateway.proxy import GatewayProxy


# =========================================================================
# Unit Tests: Frame Parsing & Structural Validation
# =========================================================================

def test_ocpp_call_parsing_and_serialization():
    """Verify standard OCPP 1.6-J CALL frame parsing and canonical serialization."""
    raw = json.dumps([2, "msg-001", "BootNotification", {"chargePointModel": "OptiCharge-400", "chargePointVendor": "EVTech"}])
    frame = OCPPFrameParser.parse_raw(raw)

    assert isinstance(frame, OCPPCall)
    assert frame.message_type_id == OCPPMessageType.CALL
    assert frame.unique_id == "msg-001"
    assert frame.action == "BootNotification"
    assert frame.payload["chargePointModel"] == "OptiCharge-400"
    assert frame.to_list() == [2, "msg-001", "BootNotification", {"chargePointModel": "OptiCharge-400", "chargePointVendor": "EVTech"}]

    # Canonical re-serialization
    re_parsed = OCPPFrameParser.parse_raw(frame.to_json())
    assert re_parsed.unique_id == frame.unique_id
    assert re_parsed.action == frame.action


def test_ocpp_call_result_parsing_and_serialization():
    """Verify standard OCPP 1.6-J CALLRESULT frame parsing and serialization."""
    raw = json.dumps([3, "msg-001", {"status": "Accepted", "currentTime": "2026-10-27T08:00:00Z", "interval": 300}])
    frame = OCPPFrameParser.parse_raw(raw)

    assert isinstance(frame, OCPPCallResult)
    assert frame.message_type_id == OCPPMessageType.CALLRESULT
    assert frame.unique_id == "msg-001"
    assert frame.payload["status"] == "Accepted"
    assert frame.to_list() == [3, "msg-001", {"status": "Accepted", "currentTime": "2026-10-27T08:00:00Z", "interval": 300}]


def test_ocpp_call_error_parsing_and_serialization():
    """Verify standard OCPP 1.6-J CALLERROR frame parsing and serialization."""
    raw = json.dumps([4, "msg-002", "FormationViolation", "Malformed charging profile structure", {"field": "chargingSchedule"}])
    frame = OCPPFrameParser.parse_raw(raw)

    assert isinstance(frame, OCPPCallError)
    assert frame.message_type_id == OCPPMessageType.CALLERROR
    assert frame.unique_id == "msg-002"
    assert frame.error_code == "FormationViolation"
    assert frame.error_description == "Malformed charging profile structure"
    assert frame.error_details == {"field": "chargingSchedule"}
    assert frame.to_list() == [4, "msg-002", "FormationViolation", "Malformed charging profile structure", {"field": "chargingSchedule"}]


def test_malformed_json_handling():
    """Verify malformed JSON raises OCPPParseError and yields FormationViolation."""
    bad_payloads = [
        "{not-json",
        "[2, 'single_quotes_invalid']",
        "[2, truncated...",
        "",
    ]
    for bad in bad_payloads:
        with pytest.raises(OCPPParseError) as exc_info:
            OCPPFrameParser.parse_raw(bad)
        assert exc_info.value.error_code == OCPPErrorCode.FormationViolation
        assert exc_info.value.can_respond_call_error is True

        err_response = exc_info.value.to_call_error()
        assert err_response.message_type_id == OCPPMessageType.CALLERROR
        assert err_response.error_code == "FormationViolation"


def test_non_array_frame_rejection():
    """Verify that JSON payloads that are not arrays are rejected with FormationViolation."""
    bad_json = [
        json.dumps({"messageTypeId": 2, "uniqueId": "123"}),
        json.dumps("just a string"),
        json.dumps(12345),
        json.dumps(True),
    ]
    for bad in bad_json:
        with pytest.raises(OCPPParseError) as exc_info:
            OCPPFrameParser.parse_raw(bad)
        assert exc_info.value.error_code == OCPPErrorCode.FormationViolation
        assert "array" in exc_info.value.description.lower()


def test_invalid_message_type_ids():
    """Verify unsupported MessageTypeIds are rejected with PropertyConstraintViolation."""
    unsupported = [
        [1, "msg-1", "SomeAction", {}],
        [5, "msg-2", "SomeAction", {}],
        [99, "msg-3", "SomeAction", {}],
    ]
    for frame_list in unsupported:
        with pytest.raises(OCPPParseError) as exc_info:
            OCPPFrameParser.parse_raw(json.dumps(frame_list))
        assert exc_info.value.error_code == OCPPErrorCode.PropertyConstraintViolation
        assert exc_info.value.unique_id == frame_list[1]


def test_boolean_message_type_id_rejection():
    """In Python, bool subclasses int (True == 1). Ensure True/False type IDs are rejected."""
    with pytest.raises(OCPPParseError) as exc_info:
        OCPPFrameParser.parse_raw(json.dumps([True, "msg-bool", "Action", {}]))
    assert exc_info.value.error_code == OCPPErrorCode.FormationViolation


def test_unsupported_frame_shapes():
    """Verify that wrong element counts are strictly rejected."""
    # CALL requires 4 elements
    with pytest.raises(OCPPParseError) as exc_info:
        OCPPFrameParser.parse_raw(json.dumps([2, "uid", "Action"]))
    assert exc_info.value.error_code == OCPPErrorCode.FormationViolation

    with pytest.raises(OCPPParseError) as exc_info:
        OCPPFrameParser.parse_raw(json.dumps([2, "uid", "Action", {}, "extra"]))
    assert exc_info.value.error_code == OCPPErrorCode.FormationViolation

    # CALLRESULT requires 3 elements
    with pytest.raises(OCPPParseError) as exc_info:
        OCPPFrameParser.parse_raw(json.dumps([3, "uid"]))
    assert exc_info.value.error_code == OCPPErrorCode.FormationViolation

    # CALLERROR requires 5 elements
    with pytest.raises(OCPPParseError) as exc_info:
        OCPPFrameParser.parse_raw(json.dumps([4, "uid", "FormationViolation"]))
    assert exc_info.value.error_code == OCPPErrorCode.FormationViolation


def test_type_and_length_constraints():
    """Verify field type constraints and UniqueId length limits (1-36 chars)."""
    # Non-string UniqueId
    with pytest.raises(OCPPParseError):
        OCPPFrameParser.parse_raw(json.dumps([2, 9999, "Heartbeat", {}]))

    # Empty UniqueId
    with pytest.raises(OCPPParseError) as exc_info:
        OCPPFrameParser.parse_raw(json.dumps([2, "", "Heartbeat", {}]))
    assert exc_info.value.error_code == OCPPErrorCode.PropertyConstraintViolation

    # UniqueId exceeding 36 characters
    with pytest.raises(OCPPParseError) as exc_info:
        OCPPFrameParser.parse_raw(json.dumps([2, "x" * 37, "Heartbeat", {}]))
    assert exc_info.value.error_code == OCPPErrorCode.PropertyConstraintViolation

    # Non-string Action
    with pytest.raises(OCPPParseError):
        OCPPFrameParser.parse_raw(json.dumps([2, "uid-1", 1234, {}]))

    # Empty Action
    with pytest.raises(OCPPParseError):
        OCPPFrameParser.parse_raw(json.dumps([2, "uid-1", "   ", {}]))

    # Non-dict Payload
    with pytest.raises(OCPPParseError):
        OCPPFrameParser.parse_raw(json.dumps([2, "uid-1", "Heartbeat", ["not-a-dict"]]))


def test_asymmetric_error_rule_enforcement():
    """
    OCPP 1.6-J Section 4.2 Asymmetry Rule:
    'A receiver MUST NOT send a CallError message in response to a CallResult or CallError message.'
    Ensure can_respond_call_error is FALSE for CALLRESULT and CALLERROR parse errors.
    """
    # Malformed CALLRESULT (too few elements)
    with pytest.raises(OCPPParseError) as exc_info_result:
        OCPPFrameParser.parse_raw(json.dumps([3, "uid-result"]))
    assert exc_info_result.value.can_respond_call_error is False

    # Malformed CALLRESULT (payload is not a dict)
    with pytest.raises(OCPPParseError) as exc_info_result2:
        OCPPFrameParser.parse_raw(json.dumps([3, "uid-result", "not-a-dict"]))
    assert exc_info_result2.value.can_respond_call_error is False

    # Malformed CALLERROR (too few elements)
    with pytest.raises(OCPPParseError) as exc_info_error:
        OCPPFrameParser.parse_raw(json.dumps([4, "uid-error", "InternalError"]))
    assert exc_info_error.value.can_respond_call_error is False

    # Malformed CALL (allowed to respond with CALLERROR)
    with pytest.raises(OCPPParseError) as exc_info_call:
        OCPPFrameParser.parse_raw(json.dumps([2, "uid-call", "Action", "not-a-dict"]))
    assert exc_info_call.value.can_respond_call_error is True


def test_max_frame_size_enforcement():
    """Verify frames exceeding the 64 KB limit are rejected."""
    # Frame with 65 KB payload
    oversized = json.dumps([2, "oversize", "MeterValues", {"data": "X" * 66000}])
    with pytest.raises(OCPPParseError) as exc_info:
        OCPPFrameParser.parse_raw(oversized, max_bytes=65536)
    assert exc_info.value.error_code == OCPPErrorCode.FormationViolation
    assert "exceeds maximum limit" in exc_info.value.description


# =========================================================================
# Unit Tests: Request Tracker & Correlation Safety
# =========================================================================

def test_request_tracker_correlation_success():
    """Verify registration and successful correlation of request and response."""
    tracker = RequestTracker()
    call = create_call("RemoteStartTransaction", {"idTag": "USER-1234"}, unique_id="req-101")

    # Charger to CSMS
    req = tracker.register_call(call, direction="CHARGER_TO_CSMS", timeout_seconds=5.0)
    assert req.unique_id == "req-101"
    assert req.sequence_token == 1
    assert tracker.pending_count == 1

    # Response comes from CSMS to Charger
    matched, err = tracker.match_response("req-101", response_direction="CSMS_TO_CHARGER")
    assert err is None
    assert matched is not None
    assert matched.unique_id == "req-101"
    assert matched.action == "RemoteStartTransaction"
    assert tracker.pending_count == 0


def test_request_tracker_direction_mismatch_rejection():
    """Verify that a response arriving from the wrong direction is rejected."""
    tracker = RequestTracker()
    call = create_call("SetChargingProfile", {}, unique_id="req-102")

    # CSMS to Charger
    tracker.register_call(call, direction="CSMS_TO_CHARGER", timeout_seconds=5.0)

    # Response incorrectly claimed to arrive from CSMS to Charger
    matched, err = tracker.match_response("req-102", response_direction="CSMS_TO_CHARGER")
    assert matched is None
    assert "direction_mismatch" in err
    # Ensure original request is NOT discarded upon mismatched direction attempt
    assert tracker.pending_count == 1


def test_request_tracker_timeout_and_late_response():
    """Verify that timed-out requests cannot be correlated with late responses."""
    tracker = RequestTracker()
    call = create_call("Heartbeat", {}, unique_id="req-103")

    now_base = 1000.0
    tracker.register_call(call, direction="CHARGER_TO_CSMS", timeout_seconds=2.0, now=now_base)

    # Correlate after 2.5 seconds (timed out)
    matched, err = tracker.match_response("req-103", response_direction="CSMS_TO_CHARGER", now=now_base + 2.5)
    assert matched is None
    assert "request_timed_out" in err
    assert tracker.pending_count == 0


def test_request_tracker_prune_expired():
    """Verify expired in-flight calls are pruned correctly."""
    tracker = RequestTracker()
    call1 = create_call("Heartbeat", {}, unique_id="h1")
    call2 = create_call("Heartbeat", {}, unique_id="h2")

    now = 500.0
    tracker.register_call(call1, direction="CHARGER_TO_CSMS", timeout_seconds=1.0, now=now)
    tracker.register_call(call2, direction="CHARGER_TO_CSMS", timeout_seconds=10.0, now=now)

    expired = tracker.prune_expired(now=now + 2.0)
    assert len(expired) == 1
    assert expired[0].unique_id == "h1"
    assert tracker.pending_count == 1


def test_request_tracker_monotonic_sequence():
    """Verify monotonic sequence tokens increment strictly."""
    tracker = RequestTracker()
    tokens = []
    for i in range(5):
        c = create_call("Heartbeat", {}, unique_id=f"seq-{i}")
        req = tracker.register_call(c, direction="CHARGER_TO_CSMS")
        tokens.append(req.sequence_token)

    assert tokens == [1, 2, 3, 4, 5]


# =========================================================================
# Integration Tests: Async WebSocket Proxy (Localhost Loopback)
# =========================================================================

def test_proxy_bidirectional_pass_through():
    """
    Integration test: Spawns a mock CSMS server, runs GatewayProxy, and connects
    a mock Charge Point. Verifies bidirectional frame pass-through and correlation.
    """
    async def _run():
        mock_csms_received = []
        mock_charger_received = []

        # Mock CSMS server on port 9201
        async def mock_csms_handler(websocket):
            async for msg in websocket:
                mock_csms_received.append(msg)
                frame = OCPPFrameParser.parse_raw(msg)
                if isinstance(frame, OCPPCall) and frame.action == "BootNotification":
                    # Reply with CALLRESULT
                    res = create_call_result(frame.unique_id, {"status": "Accepted", "interval": 60})
                    await websocket.send(res.to_json())

        csms_server = await serve(
            mock_csms_handler,
            host="127.0.0.1",
            port=9201,
            subprotocols=[Subprotocol("ocpp1.6")],
        )

        # Configure and start Gateway on ports 9200 (charger) -> 9201 (CSMS)
        config = GatewayConfig(
            host="127.0.0.1",
            charger_port=9200,
            csms_host="127.0.0.1",
            csms_port=9201,
            call_timeout_seconds=5.0,
        )
        proxy = GatewayProxy(config)
        await proxy.start()

        try:
            # Mock Charger connects to Gateway at ws://127.0.0.1:9200/CP_INT_TEST
            async with connect(
                "ws://127.0.0.1:9200/CP_INT_TEST",
                subprotocols=[Subprotocol("ocpp1.6")],
            ) as charger_ws:
                # Send BootNotification CALL
                call = create_call("BootNotification", {"chargePointModel": "ProCharge", "chargePointVendor": "ThreatLens"})
                await charger_ws.send(call.to_json())

                # Await CALLRESULT response through the gateway
                response_raw = await asyncio.wait_for(charger_ws.recv(), timeout=2.0)
                mock_charger_received.append(response_raw)

                res_frame = OCPPFrameParser.parse_raw(response_raw)
                assert isinstance(res_frame, OCPPCallResult)
                assert res_frame.unique_id == call.unique_id
                assert res_frame.payload["status"] == "Accepted"

                # Check that CSMS received the original CALL
                assert len(mock_csms_received) == 1
                csms_frame = OCPPFrameParser.parse_raw(mock_csms_received[0])
                assert csms_frame.unique_id == call.unique_id
                assert csms_frame.action == "BootNotification"

        finally:
            await proxy.stop()
            csms_server.close()
            await csms_server.wait_closed()

    asyncio.run(_run())


def test_proxy_invalid_call_returns_callerror():
    """
    Integration test: Charger sends a malformed CALL frame to Gateway.
    Gateway returns CALLERROR: FormationViolation back to charger without forwarding to CSMS.
    """
    async def _run():
        mock_csms_received = []

        async def mock_csms_handler(websocket):
            async for msg in websocket:
                mock_csms_received.append(msg)

        csms_server = await serve(
            mock_csms_handler,
            host="127.0.0.1",
            port=9211,
            subprotocols=[Subprotocol("ocpp1.6")],
        )

        config = GatewayConfig(
            host="127.0.0.1",
            charger_port=9210,
            csms_host="127.0.0.1",
            csms_port=9211,
        )
        proxy = GatewayProxy(config)
        await proxy.start()

        try:
            async with connect(
                "ws://127.0.0.1:9210/CP_ERR_TEST",
                subprotocols=[Subprotocol("ocpp1.6")],
            ) as charger_ws:
                # Send an invalid CALL frame: payload is a string instead of dict
                bad_call = json.dumps([2, "bad-call-1", "Heartbeat", "string_not_dict"])
                await charger_ws.send(bad_call)

                # Gateway should respond with CALLERROR FormationViolation
                response_raw = await asyncio.wait_for(charger_ws.recv(), timeout=2.0)
                err_frame = OCPPFrameParser.parse_raw(response_raw)

                assert isinstance(err_frame, OCPPCallError)
                assert err_frame.unique_id == "bad-call-1"
                assert err_frame.error_code == "FormationViolation"

                # CSMS must have received zero messages (dropped at gateway)
                assert len(mock_csms_received) == 0

        finally:
            await proxy.stop()
            csms_server.close()
            await csms_server.wait_closed()

    asyncio.run(_run())


def test_proxy_failsafe_disconnect_when_csms_unavailable():
    """
    Fail-Safe policy verification:
    If upstream CSMS is offline/unreachable, charger connection is closed cleanly with 1011.
    """
    async def _run():
        config = GatewayConfig(
            host="127.0.0.1",
            charger_port=9220,
            csms_host="127.0.0.1",
            csms_port=9221,  # Nothing listening here
        )
        proxy = GatewayProxy(config)
        await proxy.start()

        try:
            # Connecting to Gateway should close almost immediately due to unreachable CSMS
            with pytest.raises(websockets.exceptions.ConnectionClosed) as exc_info:
                async with connect(
                    "ws://127.0.0.1:9220/CP_FAILSAFE",
                    subprotocols=[Subprotocol("ocpp1.6")],
                ) as charger_ws:
                    await charger_ws.recv()

            assert exc_info.value.rcvd.code in (1011, 1006)
        finally:
            await proxy.stop()

    asyncio.run(_run())
