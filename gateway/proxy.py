"""
ThreatLens Asynchronous OCPP 1.6-J Security Gateway Proxy (Phase 1A).

Provides localhost-only bidirectional WebSocket forwarding between:
- Charge Point (EVSE) connecting to ws://127.0.0.1:9000/{charge_point_id}
- Central System (CSMS) running upstream on ws://127.0.0.1:9001/{charge_point_id}

Features:
- Strict subprotocol negotiation (ocpp1.6)
- Frame-level structural validation via OCPPFrameParser
- Correlation tracking and sequence verification via RequestTracker
- Maximum frame size enforcement (64 KB)
- Fail-Safe connection pairing and graceful shutdown
"""

import asyncio
import contextlib
import logging
import time
from typing import Dict, Optional, Set
import uuid

import websockets
from websockets.asyncio.client import ClientConnection, connect
from websockets.asyncio.server import Server, ServerConnection, serve
from websockets.exceptions import ConnectionClosed, PayloadTooBig
from websockets.typing import Subprotocol

from gateway.config import GatewayConfig
from gateway.models import (
    OCPPCall,
    OCPPCallError,
    OCPPCallResult,
    OCPPErrorCode,
    OCPPFrame,
    OCPPFrameParser,
    OCPPParseError,
    RequestTracker,
    create_call_error,
)
from gateway.policy import (
    GatewayPolicyEngine,
    PolicyDecision,
    PolicyEvaluationResult,
)

logger = logging.getLogger("ThreatLens.Gateway.Proxy")


class GatewaySession:
    """Manages an active paired connection between a Charger and CSMS."""

    def __init__(
        self,
        session_id: str,
        charge_point_id: str,
        charger_ws: ServerConnection,
        csms_ws: ClientConnection,
        tracker: RequestTracker,
    ):
        self.session_id = session_id
        self.charge_point_id = charge_point_id
        self.charger_ws = charger_ws
        self.csms_ws = csms_ws
        self.tracker = tracker
        self.created_at = time.monotonic()
        self.is_closing = False
        self.messages_forwarded: int = 0
        self.messages_rejected: int = 0
        self.messages_allowed: int = 0
        self.messages_clamped: int = 0
        self.messages_blocked: int = 0

    async def close(self, code: int = 1000, reason: str = "Normal Closure") -> None:
        """Close both sockets cleanly and clear correlation state."""
        if self.is_closing:
            return
        self.is_closing = True
        logger.info("[Session %s] Closing session for %s: %s", self.session_id, self.charge_point_id, reason)

        # Clear pending correlation tracking
        orphaned = self.tracker.clear()
        if orphaned:
            logger.warning("[Session %s] Cleared %d orphaned in-flight requests", self.session_id, len(orphaned))

        # Close charger socket if still open
        if self.charger_ws and self.charger_ws.state.name != "CLOSED":
            with contextlib.suppress(Exception):
                await self.charger_ws.close(code=code, reason=reason)

        # Close CSMS socket if still open
        if self.csms_ws and self.csms_ws.state.name != "CLOSED":
            with contextlib.suppress(Exception):
                await self.csms_ws.close(code=code, reason=reason)


class GatewayProxy:
    """
    ThreatLens OCPP 1.6-J Security Gateway Proxy.
    
    Accepts incoming WebSocket connections from EV chargers on charger_port (9000),
    establishes an upstream connection to the CSMS on csms_port (9001), and
    validates/forwards messages bidirectionally.
    """

    def __init__(
        self,
        config: Optional[GatewayConfig] = None,
        policy_engine: Optional[GatewayPolicyEngine] = None,
        audit_callback: Optional[Any] = None,
    ):
        self.config = config or GatewayConfig()
        self.policy_engine = policy_engine or GatewayPolicyEngine(self.config.policy)
        self.audit_callback = audit_callback
        self.server: Optional[Server] = None
        self.active_sessions: Dict[str, GatewaySession] = {}
        self.is_running: bool = False
        self._prune_task: Optional[asyncio.Task] = None
        self._server_lock = asyncio.Lock()

        # Global cumulative metrics across all sessions
        self.total_messages: int = 0
        self.total_allowed: int = 0
        self.total_clamped: int = 0
        self.total_blocked: int = 0
        self.total_errors: int = 0

    async def start(self) -> None:
        """Start the WebSocket server and background correlation pruner."""
        async with self._server_lock:
            if self.is_running:
                return
            self.is_running = True

            subprots = [Subprotocol(sp) for sp in self.config.subprotocols]
            self.server = await serve(
                self._handle_charger_connection,
                host=self.config.host,
                port=self.config.charger_port,
                subprotocols=subprots,
                max_size=self.config.max_frame_bytes,
                ping_interval=self.config.ping_interval,
                ping_timeout=self.config.ping_timeout,
                close_timeout=self.config.close_timeout,
            )
            self._prune_task = asyncio.create_task(self._prune_loop())
            logger.info(
                "ThreatLens Gateway proxy listening on ws://%s:%d (Charger endpoint)",
                self.config.host,
                self.config.charger_port,
            )
            logger.info(
                "ThreatLens Gateway upstream target ws://%s:%d (CSMS endpoint)",
                self.config.csms_host,
                self.config.csms_port,
            )

    async def stop(self) -> None:
        """Stop the proxy and disconnect all active sessions."""
        async with self._server_lock:
            if not self.is_running:
                return
            self.is_running = False

            if self._prune_task:
                self._prune_task.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await self._prune_task
                self._prune_task = None

            # Disconnect all active sessions
            for session in list(self.active_sessions.values()):
                await session.close(code=1001, reason="ThreatLens Gateway shutting down")
            self.active_sessions.clear()

            if self.server:
                self.server.close()
                await self.server.wait_closed()
                self.server = None

            logger.info("ThreatLens Gateway proxy stopped cleanly")

    async def _handle_charger_connection(self, charger_ws: ServerConnection) -> None:
        """Handle an incoming charger connection, pair with CSMS, and pump messages."""
        # Extract charge point ID from URL path (e.g., /CP_1)
        raw_path = getattr(getattr(charger_ws, "request", None), "path", "") or ""
        path = raw_path.strip("/")
        charge_point_id = path.split("/")[0] if path else "default_cp"

        session_id = f"{charge_point_id}_{uuid.uuid4().hex[:8]}"
        csms_url = f"ws://{self.config.csms_host}:{self.config.csms_port}/{charge_point_id}"

        logger.info(
            "[Session %s] Charger connected for '%s' (negotiated subprotocol: %s)",
            session_id,
            charge_point_id,
            charger_ws.subprotocol,
        )

        # Attempt upstream connection to CSMS
        try:
            csms_ws = await asyncio.wait_for(
                connect(
                    csms_url,
                    subprotocols=[Subprotocol(sp) for sp in self.config.subprotocols],
                    max_size=self.config.max_frame_bytes,
                    ping_interval=self.config.ping_interval,
                    ping_timeout=self.config.ping_timeout,
                    close_timeout=self.config.close_timeout,
                ),
                timeout=5.0,
            )
            logger.info(
                "[Session %s] Connected upstream to CSMS at %s (negotiated subprotocol: %s)",
                session_id,
                csms_url,
                csms_ws.subprotocol,
            )
        except Exception as exc:
            logger.error("[Session %s] Failed to connect upstream to CSMS at %s: %s", session_id, csms_url, exc)
            # Fail-Safe policy: Close charger connection if CSMS is unreachable
            await charger_ws.close(code=1011, reason="Upstream CSMS unavailable")
            return

        session = GatewaySession(
            session_id=session_id,
            charge_point_id=charge_point_id,
            charger_ws=charger_ws,
            csms_ws=csms_ws,
            tracker=RequestTracker(),
        )
        self.active_sessions[session_id] = session

        # Run bidirectional message pumping
        charger_to_csms_task = asyncio.create_task(
            self._pump_messages(charger_ws, csms_ws, "CHARGER_TO_CSMS", session)
        )
        csms_to_charger_task = asyncio.create_task(
            self._pump_messages(csms_ws, charger_ws, "CSMS_TO_CHARGER", session)
        )

        try:
            done, pending = await asyncio.wait(
                [charger_to_csms_task, csms_to_charger_task],
                return_when=asyncio.FIRST_COMPLETED,
            )
            for task in pending:
                task.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await task
        finally:
            await session.close(code=1000, reason="Connection terminated")
            self.active_sessions.pop(session_id, None)
            logger.info(
                "[Session %s] Terminated (forwarded: %d, rejected: %d)",
                session_id,
                session.messages_forwarded,
                session.messages_rejected,
            )

    async def _pump_messages(
        self,
        source_ws: ServerConnection | ClientConnection,
        target_ws: ServerConnection | ClientConnection,
        direction: str,
        session: GatewaySession,
    ) -> None:
        """Pumps messages from source_ws to target_ws with framing validation and correlation."""
        try:
            async for raw_message in source_ws:
                # 1. Byte size enforcement
                if len(raw_message) > self.config.max_frame_bytes:
                    logger.warning(
                        "[%s:%s] Message size (%d bytes) exceeds max limit (%d bytes)",
                        session.charge_point_id,
                        direction,
                        len(raw_message),
                        self.config.max_frame_bytes,
                    )
                    session.messages_rejected += 1
                    await source_ws.close(code=1009, reason="Message exceeds 64KB maximum limit")
                    break

                # 2. Strict OCPP 1.6-J frame parsing
                try:
                    frame = OCPPFrameParser.parse_raw(raw_message, max_bytes=self.config.max_frame_bytes)
                except OCPPParseError as err:
                    session.messages_rejected += 1
                    logger.warning(
                        "[%s:%s] Parse violation: %s (ErrorCode=%s, can_respond=%s)",
                        session.charge_point_id,
                        direction,
                        err.description,
                        err.error_code,
                        err.can_respond_call_error,
                    )
                    if err.can_respond_call_error:
                        # Return CALLERROR to sender (allowed only for CALL violations)
                        call_err = err.to_call_error()
                        with contextlib.suppress(Exception):
                            await source_ws.send(call_err.to_json())
                    # Discard invalid frame
                    continue
                except Exception as exc:
                    session.messages_rejected += 1
                    logger.exception(
                        "[%s:%s] Unexpected exception during framing: %s",
                        session.charge_point_id,
                        direction,
                        exc,
                    )
                    continue

                # 3. Policy Evaluation on CALL messages
                if isinstance(frame, OCPPCall):
                    self.total_messages += 1
                    policy_res = self.policy_engine.evaluate_call(
                        call=frame,
                        direction=direction,
                        charge_point_id=session.charge_point_id,
                    )

                    # Dispatch audit event if callback registered
                    if self.audit_callback:
                        try:
                            self.audit_callback({
                                "timestamp": policy_res.timestamp,
                                "charge_point_id": session.charge_point_id,
                                "unique_id": frame.unique_id,
                                "action": frame.action,
                                "direction": direction,
                                "decision": policy_res.decision.value,
                                "rule_id": policy_res.rule_id,
                                "reason": policy_res.reason,
                                "original_limit": policy_res.original_limit,
                                "modified_limit": policy_res.modified_limit,
                                "error_code": policy_res.error_code.value if policy_res.error_code else None,
                            })
                        except Exception as audit_err:
                            logger.warning("[%s] Audit callback exception: %s", session.charge_point_id, audit_err)

                    if policy_res.decision == PolicyDecision.BLOCK:
                        session.messages_blocked += 1
                        self.total_blocked += 1
                        logger.warning(
                            "[%s:%s] Policy BLOCK on %s [%s]: %s (%s)",
                            session.charge_point_id,
                            direction,
                            frame.action,
                            frame.unique_id,
                            policy_res.reason,
                            policy_res.rule_id,
                        )
                        err_code = policy_res.error_code or OCPPErrorCode.SecurityError
                        call_err = create_call_error(
                            unique_id=frame.unique_id,
                            error_code=err_code,
                            description=policy_res.reason,
                            details={"rule_id": policy_res.rule_id},
                        )
                        with contextlib.suppress(Exception):
                            await source_ws.send(call_err.to_json())
                        # Drop frame: do NOT forward to target_ws
                        continue

                    elif policy_res.decision == PolicyDecision.CLAMP:
                        session.messages_clamped += 1
                        self.total_clamped += 1
                        logger.info(
                            "[%s:%s] Policy CLAMP on %s [%s]: %sA -> %sA (%s)",
                            session.charge_point_id,
                            direction,
                            frame.action,
                            frame.unique_id,
                            policy_res.original_limit,
                            policy_res.modified_limit,
                            policy_res.rule_id,
                        )
                        if policy_res.modified_payload:
                            frame.payload = policy_res.modified_payload

                    elif policy_res.decision == PolicyDecision.ALLOW:
                        session.messages_allowed += 1
                        self.total_allowed += 1

                    # Register in correlation tracker
                    session.tracker.register_call(
                        frame,
                        direction=direction,
                        timeout_seconds=self.config.call_timeout_seconds,
                    )
                    logger.debug(
                        "[%s:%s] CALL [%s] Action=%s registered",
                        session.charge_point_id,
                        direction,
                        frame.unique_id,
                        frame.action,
                    )

                elif isinstance(frame, (OCPPCallResult, OCPPCallError)):
                    self.total_messages += 1
                    matched_req, err_reason = session.tracker.match_response(
                        unique_id=frame.unique_id,
                        response_direction=direction,
                    )
                    if err_reason:
                        session.messages_rejected += 1
                        self.total_errors += 1
                        logger.warning(
                            "[%s:%s] Response correlation failed for [%s]: %s (dropping frame)",
                            session.charge_point_id,
                            direction,
                            frame.unique_id,
                            err_reason,
                        )
                        # Asymmetry rule: NEVER respond with CALLERROR to a CALLRESULT or CALLERROR
                        continue

                    latency = time.monotonic() - matched_req.created_at
                    logger.debug(
                        "[%s:%s] Response [%s] matched Action=%s (latency=%.3fs)",
                        session.charge_point_id,
                        direction,
                        frame.unique_id,
                        matched_req.action,
                        latency,
                    )

                # 4. Message Forwarding
                # Forward canonical JSON frame to target endpoint
                await target_ws.send(frame.to_json())
                session.messages_forwarded += 1

        except (ConnectionClosed, PayloadTooBig):
            pass
        except Exception as exc:
            logger.warning("[%s:%s] Pump error: %s", session.charge_point_id, direction, exc)

    async def _prune_loop(self) -> None:
        """Periodically prune timed-out in-flight requests from all active sessions."""
        while self.is_running:
            try:
                await asyncio.sleep(self.config.prune_interval_seconds)
                for session in list(self.active_sessions.values()):
                    expired = session.tracker.prune_expired()
                    if expired:
                        logger.warning(
                            "[%s] Pruned %d expired in-flight requests: %s",
                            session.charge_point_id,
                            len(expired),
                            [req.unique_id for req in expired],
                        )
            except asyncio.CancelledError:
                break
            except Exception as exc:
                logger.warning("[Proxy] Prune loop exception: %s", exc)
