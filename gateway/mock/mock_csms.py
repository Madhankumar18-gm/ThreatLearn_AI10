"""
ThreatLens Local Mock CSMS (Central System) Implementation.

Listens on localhost (default port 9001) as an OCPP 1.6-J Central System.
Handles standard charger notifications and allows injecting downstream commands
for automated scenario testing.
"""

import asyncio
import contextlib
import json
import logging
from typing import Any, Dict, List, Optional
import uuid

from websockets.asyncio.server import Server, ServerConnection, serve
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

logger = logging.getLogger("ThreatLens.Mock.CSMS")


class MockCSMS:
    """Mock Central System Management Service for localhost testing."""

    def __init__(self, host: str = "127.0.0.1", port: int = 9001):
        self.host = host
        self.port = port
        self.server: Optional[Server] = None
        self.is_running: bool = False
        self.connections: Dict[str, ServerConnection] = {}
        self.received_frames: List[OCPPFrame] = []
        self.sent_frames: List[OCPPFrame] = []
        self._response_waiters: Dict[str, asyncio.Future] = {}
        self._new_connection_event = asyncio.Event()

    async def start(self) -> None:
        """Start the mock CSMS WebSocket server."""
        if self.is_running:
            return
        self.is_running = True
        self.server = await serve(
            self._handle_connection,
            host=self.host,
            port=self.port,
            subprotocols=[Subprotocol("ocpp1.6")],
        )
        logger.info("Mock CSMS listening on ws://%s:%d", self.host, self.port)

    async def stop(self) -> None:
        """Stop the mock CSMS server and close connections."""
        if not self.is_running:
            return
        self.is_running = False
        for cp_id, ws in list(self.connections.items()):
            with contextlib.suppress(Exception):
                await ws.close(1000, "Mock CSMS stopping")
        self.connections.clear()
        if self.server:
            self.server.close()
            await self.server.wait_closed()
            self.server = None
        logger.info("Mock CSMS stopped cleanly")

    async def wait_for_connection(self, charge_point_id: str, timeout: float = 3.0) -> ServerConnection:
        """Wait until the specified charge point connects upstream."""
        start_time = asyncio.get_event_loop().time()
        while (asyncio.get_event_loop().time() - start_time) < timeout:
            if charge_point_id in self.connections:
                return self.connections[charge_point_id]
            self._new_connection_event.clear()
            with contextlib.suppress(asyncio.TimeoutError):
                await asyncio.wait_for(self._new_connection_event.wait(), timeout=0.1)
        if charge_point_id in self.connections:
            return self.connections[charge_point_id]
        raise TimeoutError(f"Charge point '{charge_point_id}' did not connect within {timeout}s")

    async def send_call(
        self,
        charge_point_id: str,
        action: str,
        payload: Dict[str, Any],
        unique_id: Optional[str] = None,
        timeout: float = 4.0,
    ) -> OCPPCallResult | OCPPCallError:
        """
        Send a CALL downstream to a connected charger and await its CALLRESULT or CALLERROR.
        """
        ws = self.connections.get(charge_point_id)
        if not ws:
            raise ConnectionError(f"No active connection for charge point '{charge_point_id}'")

        call = create_call(action=action, payload=payload, unique_id=unique_id)
        loop = asyncio.get_running_loop()
        future: asyncio.Future = loop.create_future()
        self._response_waiters[call.unique_id] = future

        await ws.send(call.to_json())
        self.sent_frames.append(call)

        try:
            response = await asyncio.wait_for(future, timeout=timeout)
            return response
        finally:
            self._response_waiters.pop(call.unique_id, None)

    async def send_raw(self, charge_point_id: str, raw_text: str) -> None:
        """Send arbitrary raw text to test malformed frames."""
        ws = self.connections.get(charge_point_id)
        if not ws:
            raise ConnectionError(f"No active connection for charge point '{charge_point_id}'")
        await ws.send(raw_text)

    async def _handle_connection(self, websocket: ServerConnection) -> None:
        """Handle incoming connection from Gateway."""
        raw_path = getattr(getattr(websocket, "request", None), "path", "") or ""
        path = raw_path.strip("/")
        charge_point_id = path.split("/")[0] if path else "default_cp"

        self.connections[charge_point_id] = websocket
        self._new_connection_event.set()
        logger.info("Mock CSMS accepted connection for '%s'", charge_point_id)

        try:
            async for message in websocket:
                try:
                    frame = OCPPFrameParser.parse_raw(message)
                    self.received_frames.append(frame)

                    if isinstance(frame, OCPPCall):
                        # Auto-respond to standard charger calls
                        await self._auto_respond_call(websocket, frame)
                    elif isinstance(frame, (OCPPCallResult, OCPPCallError)):
                        # Deliver to awaiting send_call future if present
                        fut = self._response_waiters.get(frame.unique_id)
                        if fut and not fut.done():
                            fut.set_result(frame)

                except Exception as exc:
                    logger.warning("Mock CSMS frame error: %s", exc)

        except ConnectionClosed:
            pass
        finally:
            self.connections.pop(charge_point_id, None)
            logger.info("Mock CSMS connection closed for '%s'", charge_point_id)

    async def _auto_respond_call(self, ws: ServerConnection, call: OCPPCall) -> None:
        """Synthesize standard OCPP 1.6-J responses for charger-initiated calls."""
        action = call.action
        payload: Dict[str, Any] = {}

        if action == "BootNotification":
            payload = {
                "status": "Accepted",
                "currentTime": "2026-10-27T08:00:00Z",
                "interval": 300,
            }
        elif action == "Heartbeat":
            payload = {"currentTime": "2026-10-27T08:00:00Z"}
        elif action == "StatusNotification":
            payload = {}
        elif action == "MeterValues":
            payload = {}
        elif action == "Authorize":
            payload = {"idTagInfo": {"status": "Accepted"}}
        elif action == "StartTransaction":
            payload = {"transactionId": 1001, "idTagInfo": {"status": "Accepted"}}
        elif action == "StopTransaction":
            payload = {"idTagInfo": {"status": "Accepted"}}
        else:
            payload = {"status": "Accepted"}

        result = create_call_result(call.unique_id, payload)
        await ws.send(result.to_json())
        self.sent_frames.append(result)
