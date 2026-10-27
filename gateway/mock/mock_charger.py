"""
ThreatLens Local Mock Charge Point (EVSE) Implementation.

Connects to the ThreatLens Security Gateway on port 9000 as an OCPP 1.6-J client.
Maintains state machine transitions, responds to downstream profile setpoints,
and records all received commands for scenario verification.
"""

import asyncio
import contextlib
import logging
from typing import Any, Dict, List, Optional
import uuid

from websockets.asyncio.client import ClientConnection, connect
from websockets.exceptions import ConnectionClosed
from websockets.typing import Subprotocol

from gateway.models import (
    OCPPCall,
    OCPPCallError,
    OCPPCallResult,
    OCPPFrame,
    OCPPFrameParser,
    create_call,
    create_call_result,
)

logger = logging.getLogger("ThreatLens.Mock.Charger")


class MockChargePoint:
    """Mock EVSE Charge Point client for automated scenario testing."""

    def __init__(
        self,
        charge_point_id: str = "CP_SIM_01",
        gateway_host: str = "127.0.0.1",
        gateway_port: int = 9000,
    ):
        self.charge_point_id = charge_point_id
        self.gateway_host = gateway_host
        self.gateway_port = gateway_port
        self.ws: Optional[ClientConnection] = None
        self.is_connected: bool = False

        # Physical & Operating state
        self.status: str = "Available"
        self.active_limit: float = 80.0
        self.active_transaction_id: Optional[int] = None
        self.temperature_c: float = 25.0

        # Message history & correlation
        self.received_calls: List[OCPPCall] = []
        self.received_results: List[OCPPCallResult] = []
        self.received_errors: List[OCPPCallError] = []
        self.sent_frames: List[OCPPFrame] = []
        self._response_waiters: Dict[str, asyncio.Future] = {}
        self._recv_task: Optional[asyncio.Task] = None

    async def connect(self, timeout: float = 4.0) -> None:
        """Connect to the ThreatLens Security Gateway."""
        if self.is_connected:
            return
        url = f"ws://{self.gateway_host}:{self.gateway_port}/{self.charge_point_id}"
        self.ws = await asyncio.wait_for(
            connect(url, subprotocols=[Subprotocol("ocpp1.6")]),
            timeout=timeout,
        )
        self.is_connected = True
        self._recv_task = asyncio.create_task(self._recv_loop())
        logger.info("Mock Charger connected to Gateway at %s", url)

    async def disconnect(self) -> None:
        """Disconnect from Gateway cleanly."""
        if not self.is_connected:
            return
        self.is_connected = False
        if self._recv_task:
            self._recv_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._recv_task
            self._recv_task = None
        if self.ws:
            with contextlib.suppress(Exception):
                await self.ws.close(1000, "Mock Charger disconnecting")
            self.ws = None
        logger.info("Mock Charger '%s' disconnected", self.charge_point_id)

    async def send_call(
        self,
        action: str,
        payload: Dict[str, Any],
        unique_id: Optional[str] = None,
        timeout: float = 4.0,
    ) -> OCPPCallResult | OCPPCallError:
        """Send an outbound CALL to CSMS and await its response."""
        if not self.ws or not self.is_connected:
            raise ConnectionError("Mock Charger is not connected")

        call = create_call(action=action, payload=payload, unique_id=unique_id)
        loop = asyncio.get_running_loop()
        future: asyncio.Future = loop.create_future()
        self._response_waiters[call.unique_id] = future

        await self.ws.send(call.to_json())
        self.sent_frames.append(call)

        try:
            return await asyncio.wait_for(future, timeout=timeout)
        finally:
            self._response_waiters.pop(call.unique_id, None)

    async def send_raw(self, raw_text: str) -> None:
        """Send raw string to test malformed message handling."""
        if not self.ws or not self.is_connected:
            raise ConnectionError("Mock Charger is not connected")
        await self.ws.send(raw_text)

    async def send_boot_notification(self, model: str = "OptiCharge-400", vendor: str = "ThreatLens") -> OCPPCallResult:
        """Send standard BootNotification call."""
        res = await self.send_call(
            "BootNotification",
            {"chargePointModel": model, "chargePointVendor": vendor},
        )
        if isinstance(res, OCPPCallResult):
            self.status = "Available"
        return res

    async def send_status_notification(self, status: str = "Available") -> OCPPCallResult:
        """Send StatusNotification."""
        self.status = status
        return await self.send_call(
            "StatusNotification",
            {"connectorId": 1, "errorCode": "NoError", "status": status},
        )

    async def send_meter_values(self, current_a: float = 80.0, temp_c: float = 25.0) -> OCPPCallResult:
        """Send MeterValues telemetry."""
        self.temperature_c = temp_c
        payload = {
            "connectorId": 1,
            "meterValue": [
                {
                    "timestamp": "2026-10-27T08:00:00Z",
                    "sampledValue": [
                        {"measurand": "Current.Import", "value": str(current_a), "unit": "A"},
                        {"measurand": "Temperature", "value": str(temp_c), "unit": "Celsius"},
                    ],
                }
            ],
        }
        return await self.send_call("MeterValues", payload)

    async def _recv_loop(self) -> None:
        """Continuously receive downstream commands from Gateway / CSMS."""
        try:
            while self.is_connected and self.ws:
                message = await self.ws.recv()
                try:
                    frame = OCPPFrameParser.parse_raw(message)
                    if isinstance(frame, OCPPCall):
                        self.received_calls.append(frame)
                        await self._handle_downstream_call(frame)
                    elif isinstance(frame, OCPPCallResult):
                        self.received_results.append(frame)
                        fut = self._response_waiters.get(frame.unique_id)
                        if fut and not fut.done():
                            fut.set_result(frame)
                    elif isinstance(frame, OCPPCallError):
                        self.received_errors.append(frame)
                        fut = self._response_waiters.get(frame.unique_id)
                        if fut and not fut.done():
                            fut.set_result(frame)
                except Exception as exc:
                    logger.warning("Mock Charger frame parse error: %s", exc)

        except (ConnectionClosed, asyncio.CancelledError):
            pass

    async def _handle_downstream_call(self, call: OCPPCall) -> None:
        """Handle downstream commands from CSMS and respond with CALLRESULT."""
        action = call.action
        payload = call.payload or {}
        reply_payload: Dict[str, Any] = {"status": "Accepted"}

        if action == "SetChargingProfile":
            # Extract setpoint limit
            limit = None
            if "limit" in payload:
                limit = float(payload["limit"])
            else:
                try:
                    limit = float(
                        payload["csChargingProfiles"]["chargingSchedule"]["chargingSchedulePeriod"][0]["limit"]
                    )
                except Exception:
                    pass

            if limit is not None:
                self.active_limit = limit
                logger.info("Mock Charger '%s' updated active limit to %.1f A", self.charge_point_id, limit)

        elif action == "RemoteStartTransaction":
            self.status = "Charging"
            self.active_transaction_id = 1001

        elif action == "RemoteStopTransaction":
            self.status = "Available"
            self.active_transaction_id = None

        res = create_call_result(call.unique_id, reply_payload)
        if self.ws:
            await self.ws.send(res.to_json())
            self.sent_frames.append(res)
