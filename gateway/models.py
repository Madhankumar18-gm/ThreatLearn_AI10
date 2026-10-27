"""
ThreatLens OCPP 1.6-J Framing and Data Models (Phase 1A).

Implements strict OCPP 1.6 JSON specification framing:
- CALL (TypeId 2): [2, "<UniqueId>", "<Action>", {<Payload>}]
- CALLRESULT (TypeId 3): [3, "<UniqueId>", {<Payload>}]
- CALLERROR (TypeId 4): [4, "<UniqueId>", "<ErrorCode>", "<ErrorDescription>", {<ErrorDetails>}]

Adheres strictly to OCPP 1.6-J Section 4 RPC error semantics:
- Standardized ErrorCodes
- Asymmetric error prohibition (Never send CALLERROR in response to CALLRESULT or CALLERROR)
- Request-response correlation and monotonic sequence tracking
"""

from dataclasses import dataclass, field
from enum import Enum, IntEnum
import json
import re
import time
from typing import Any, Dict, List, Optional, Tuple
import uuid


class OCPPMessageType(IntEnum):
    """OCPP 1.6-J RPC Message Type Identifiers."""
    CALL = 2
    CALLRESULT = 3
    CALLERROR = 4


class OCPPErrorCode(str, Enum):
    """
    Standard OCPP 1.6-J RPC Error Codes (Section 4.2.3).
    All error codes defined by the official specification.
    """
    FormationViolation = "FormationViolation"
    PropertyConstraintViolation = "PropertyConstraintViolation"
    OccurenceConstraintViolation = "OccurenceConstraintViolation"
    TypeConstraintViolation = "TypeConstraintViolation"
    SecurityError = "SecurityError"
    NotImplemented = "NotImplemented"
    NotSupported = "NotSupported"
    ProtocolError = "ProtocolError"
    InternalError = "InternalError"
    GenericError = "GenericError"


@dataclass
class OCPPFrame:
    """Base class for parsed OCPP 1.6-J frames."""
    message_type_id: OCPPMessageType
    unique_id: str

    def to_list(self) -> List[Any]:
        raise NotImplementedError

    def to_json(self) -> str:
        return json.dumps(self.to_list(), separators=(",", ":"))


@dataclass
class OCPPCall(OCPPFrame):
    """
    OCPP 1.6-J CALL Frame.
    Format: [2, "<UniqueId>", "<Action>", {<Payload>}]
    """
    action: str = ""
    payload: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        self.message_type_id = OCPPMessageType.CALL

    def to_list(self) -> List[Any]:
        return [int(self.message_type_id), self.unique_id, self.action, self.payload]


@dataclass
class OCPPCallResult(OCPPFrame):
    """
    OCPP 1.6-J CALLRESULT Frame.
    Format: [3, "<UniqueId>", {<Payload>}]
    """
    payload: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        self.message_type_id = OCPPMessageType.CALLRESULT

    def to_list(self) -> List[Any]:
        return [int(self.message_type_id), self.unique_id, self.payload]


@dataclass
class OCPPCallError(OCPPFrame):
    """
    OCPP 1.6-J CALLERROR Frame.
    Format: [4, "<UniqueId>", "<ErrorCode>", "<ErrorDescription>", {<ErrorDetails>}]
    """
    error_code: str = OCPPErrorCode.GenericError.value
    error_description: str = ""
    error_details: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        self.message_type_id = OCPPMessageType.CALLERROR

    def to_list(self) -> List[Any]:
        return [
            int(self.message_type_id),
            self.unique_id,
            self.error_code,
            self.error_description,
            self.error_details,
        ]


class OCPPParseError(Exception):
    """
    Raised when an incoming frame violates OCPP 1.6-J JSON framing syntax or constraints.
    
    Attributes:
        unique_id: Extracted unique ID (or empty string if unidentifiable).
        error_code: Standard OCPPErrorCode to report if a CALLERROR is permitted.
        description: Human-readable error description.
        details: Diagnostic details dictionary.
        can_respond_call_error: If True, gateway may respond with CALLERROR.
                                If False (e.g. frame was CALLRESULT or CALLERROR),
                                Section 4.2 strictly forbids returning CALLERROR.
    """
    def __init__(
        self,
        description: str,
        unique_id: str = "",
        error_code: OCPPErrorCode = OCPPErrorCode.FormationViolation,
        details: Optional[Dict[str, Any]] = None,
        can_respond_call_error: bool = True,
    ):
        super().__init__(description)
        self.description = description
        self.unique_id = unique_id
        self.error_code = error_code
        self.details = details or {}
        self.can_respond_call_error = can_respond_call_error

    def to_call_error(self) -> OCPPCallError:
        """Construct an OCPPCallError from this parse exception."""
        return OCPPCallError(
            message_type_id=OCPPMessageType.CALLERROR,
            unique_id=self.unique_id or "",
            error_code=self.error_code.value if isinstance(self.error_code, OCPPErrorCode) else str(self.error_code),
            error_description=self.description,
            error_details=self.details,
        )


class OCPPFrameParser:
    """
    Strict parser and structural validator for OCPP 1.6-J frames.
    """

    @staticmethod
    def parse_raw(raw_data: str | bytes, max_bytes: int = 65536) -> OCPPCall | OCPPCallResult | OCPPCallError:
        """
        Parse raw WebSocket text or binary payload into an OCPPFrame.
        
        Args:
            raw_data: Incoming message string or bytes.
            max_bytes: Maximum allowed byte size (default 64 KB).
            
        Returns:
            Parsed OCPPCall, OCPPCallResult, or OCPPCallError.
            
        Raises:
            OCPPParseError: On any syntax, structural, or constraint violation.
        """
        # 1. Enforce payload size limit
        if len(raw_data) > max_bytes:
            raise OCPPParseError(
                description=f"Payload size ({len(raw_data)} bytes) exceeds maximum limit ({max_bytes} bytes)",
                unique_id="",
                error_code=OCPPErrorCode.FormationViolation,
                can_respond_call_error=True,
            )

        # 2. Decode string
        if isinstance(raw_data, bytes):
            try:
                text = raw_data.decode("utf-8")
            except UnicodeDecodeError as exc:
                raise OCPPParseError(
                    description=f"Invalid UTF-8 encoding in message: {exc}",
                    unique_id="",
                    error_code=OCPPErrorCode.FormationViolation,
                    can_respond_call_error=True,
                ) from exc
        else:
            text = raw_data

        # 3. Parse JSON
        try:
            data = json.loads(text)
        except json.JSONDecodeError as exc:
            # Try to extract MessageTypeId and UniqueId if possible using regex for informative error
            match = re.search(r'\[\s*(2|3|4)\s*,\s*"([^"]{1,36})"', text)
            uid = ""
            can_respond = True
            if match:
                type_str, uid = match.group(1), match.group(2)
                if type_str in ("3", "4"):
                    can_respond = False
            raise OCPPParseError(
                description=f"Malformed JSON: {exc.msg} at line {exc.lineno} col {exc.colno}",
                unique_id=uid,
                error_code=OCPPErrorCode.FormationViolation,
                details={"position": exc.pos, "lineno": exc.lineno, "colno": exc.colno},
                can_respond_call_error=can_respond,
            ) from exc

        # 4. Enforce JSON array structure
        if not isinstance(data, list):
            raise OCPPParseError(
                description="OCPP frame must be a JSON array",
                unique_id="",
                error_code=OCPPErrorCode.FormationViolation,
                details={"received_type": type(data).__name__},
                can_respond_call_error=True,
            )

        # Check if frame identifies as CALLRESULT (3) or CALLERROR (4) for asymmetry rule
        can_respond = True
        uid = ""
        if len(data) >= 1:
            raw_t = data[0]
            if not isinstance(raw_t, bool) and raw_t in (OCPPMessageType.CALLRESULT, OCPPMessageType.CALLERROR, 3, 4):
                can_respond = False
        if len(data) >= 2 and isinstance(data[1], str):
            uid = data[1]

        # 5. Enforce minimum length
        if len(data) < 3:
            raise OCPPParseError(
                description=f"OCPP frame array too short ({len(data)} elements, minimum 3 required)",
                unique_id=uid,
                error_code=OCPPErrorCode.FormationViolation,
                details={"array_length": len(data)},
                can_respond_call_error=can_respond,
            )

        # 6. Validate MessageTypeId
        raw_type = data[0]
        # In Python, bool is a subclass of int (True == 1), so check explicitly
        if not isinstance(raw_type, int) or isinstance(raw_type, bool):
            raise OCPPParseError(
                description=f"MessageTypeId must be an integer, got {type(raw_type).__name__}",
                unique_id="",
                error_code=OCPPErrorCode.FormationViolation,
                can_respond_call_error=True,
            )

        if raw_type not in (OCPPMessageType.CALL, OCPPMessageType.CALLRESULT, OCPPMessageType.CALLERROR):
            uid = str(data[1]) if len(data) > 1 and isinstance(data[1], str) else ""
            raise OCPPParseError(
                description=f"Unsupported MessageTypeId: {raw_type} (allowed: 2=CALL, 3=CALLRESULT, 4=CALLERROR)",
                unique_id=uid,
                error_code=OCPPErrorCode.PropertyConstraintViolation,
                details={"received_type_id": raw_type},
                can_respond_call_error=True,
            )

        msg_type = OCPPMessageType(raw_type)

        # 7. Validate CALL (TypeId 2)
        if msg_type == OCPPMessageType.CALL:
            if len(data) != 4:
                uid = str(data[1]) if len(data) > 1 and isinstance(data[1], str) else ""
                raise OCPPParseError(
                    description=f"CALL frame must have exactly 4 elements [2, UniqueId, Action, Payload], got {len(data)}",
                    unique_id=uid,
                    error_code=OCPPErrorCode.FormationViolation,
                    can_respond_call_error=True,
                )

            # UniqueId check
            unique_id = data[1]
            if not isinstance(unique_id, str):
                raise OCPPParseError(
                    description=f"UniqueId must be a string, got {type(unique_id).__name__}",
                    unique_id="",
                    error_code=OCPPErrorCode.FormationViolation,
                    can_respond_call_error=True,
                )
            if len(unique_id) == 0 or len(unique_id) > 36:
                raise OCPPParseError(
                    description=f"UniqueId length must be between 1 and 36 characters (got {len(unique_id)})",
                    unique_id=unique_id[:36],
                    error_code=OCPPErrorCode.PropertyConstraintViolation,
                    can_respond_call_error=True,
                )

            # Action check
            action = data[2]
            if not isinstance(action, str):
                raise OCPPParseError(
                    description=f"Action must be a string, got {type(action).__name__}",
                    unique_id=unique_id,
                    error_code=OCPPErrorCode.FormationViolation,
                    can_respond_call_error=True,
                )
            if len(action.strip()) == 0:
                raise OCPPParseError(
                    description="Action must not be empty",
                    unique_id=unique_id,
                    error_code=OCPPErrorCode.PropertyConstraintViolation,
                    can_respond_call_error=True,
                )

            # Payload check
            payload = data[3]
            if not isinstance(payload, dict):
                raise OCPPParseError(
                    description=f"Payload must be a JSON object, got {type(payload).__name__}",
                    unique_id=unique_id,
                    error_code=OCPPErrorCode.FormationViolation,
                    can_respond_call_error=True,
                )

            return OCPPCall(
                message_type_id=OCPPMessageType.CALL,
                unique_id=unique_id,
                action=action,
                payload=payload,
            )

        # 8. Validate CALLRESULT (TypeId 3)
        # Asymmetry rule: can_respond_call_error is FALSE for CALLRESULT violations
        if msg_type == OCPPMessageType.CALLRESULT:
            if len(data) != 3:
                uid = str(data[1]) if len(data) > 1 and isinstance(data[1], str) else ""
                raise OCPPParseError(
                    description=f"CALLRESULT frame must have exactly 3 elements [3, UniqueId, Payload], got {len(data)}",
                    unique_id=uid,
                    error_code=OCPPErrorCode.FormationViolation,
                    can_respond_call_error=False,
                )

            unique_id = data[1]
            if not isinstance(unique_id, str):
                raise OCPPParseError(
                    description=f"CALLRESULT UniqueId must be a string, got {type(unique_id).__name__}",
                    unique_id="",
                    error_code=OCPPErrorCode.FormationViolation,
                    can_respond_call_error=False,
                )
            if len(unique_id) == 0 or len(unique_id) > 36:
                raise OCPPParseError(
                    description=f"CALLRESULT UniqueId length must be between 1 and 36 characters (got {len(unique_id)})",
                    unique_id=unique_id[:36],
                    error_code=OCPPErrorCode.PropertyConstraintViolation,
                    can_respond_call_error=False,
                )

            payload = data[2]
            if not isinstance(payload, dict):
                raise OCPPParseError(
                    description=f"CALLRESULT Payload must be a JSON object, got {type(payload).__name__}",
                    unique_id=unique_id,
                    error_code=OCPPErrorCode.FormationViolation,
                    can_respond_call_error=False,
                )

            return OCPPCallResult(
                message_type_id=OCPPMessageType.CALLRESULT,
                unique_id=unique_id,
                payload=payload,
            )

        # 9. Validate CALLERROR (TypeId 4)
        # Asymmetry rule: can_respond_call_error is FALSE for CALLERROR violations
        if msg_type == OCPPMessageType.CALLERROR:
            if len(data) != 5:
                uid = str(data[1]) if len(data) > 1 and isinstance(data[1], str) else ""
                raise OCPPParseError(
                    description=f"CALLERROR frame must have exactly 5 elements [4, UniqueId, ErrorCode, ErrorDescription, ErrorDetails], got {len(data)}",
                    unique_id=uid,
                    error_code=OCPPErrorCode.FormationViolation,
                    can_respond_call_error=False,
                )

            unique_id = data[1]
            if not isinstance(unique_id, str):
                raise OCPPParseError(
                    description=f"CALLERROR UniqueId must be a string, got {type(unique_id).__name__}",
                    unique_id="",
                    error_code=OCPPErrorCode.FormationViolation,
                    can_respond_call_error=False,
                )

            error_code = data[2]
            if not isinstance(error_code, str):
                raise OCPPParseError(
                    description=f"CALLERROR ErrorCode must be a string, got {type(error_code).__name__}",
                    unique_id=unique_id,
                    error_code=OCPPErrorCode.FormationViolation,
                    can_respond_call_error=False,
                )

            error_description = data[3]
            if not isinstance(error_description, str):
                raise OCPPParseError(
                    description=f"CALLERROR ErrorDescription must be a string, got {type(error_description).__name__}",
                    unique_id=unique_id,
                    error_code=OCPPErrorCode.FormationViolation,
                    can_respond_call_error=False,
                )

            error_details = data[4]
            if not isinstance(error_details, dict):
                raise OCPPParseError(
                    description=f"CALLERROR ErrorDetails must be a JSON object, got {type(error_details).__name__}",
                    unique_id=unique_id,
                    error_code=OCPPErrorCode.FormationViolation,
                    can_respond_call_error=False,
                )

            return OCPPCallError(
                message_type_id=OCPPMessageType.CALLERROR,
                unique_id=unique_id,
                error_code=error_code,
                error_description=error_description,
                error_details=error_details,
            )

        raise OCPPParseError(
            description=f"Unrecognized message type: {raw_type}",
            unique_id="",
            error_code=OCPPErrorCode.InternalError,
            can_respond_call_error=True,
        )


def create_call(action: str, payload: Dict[str, Any], unique_id: Optional[str] = None) -> OCPPCall:
    """Helper to create a well-formed OCPP 1.6-J CALL frame."""
    uid = unique_id if unique_id else uuid.uuid4().hex
    return OCPPCall(
        message_type_id=OCPPMessageType.CALL,
        unique_id=uid,
        action=action,
        payload=payload,
    )


def create_call_result(unique_id: str, payload: Dict[str, Any]) -> OCPPCallResult:
    """Helper to create a well-formed OCPP 1.6-J CALLRESULT frame."""
    return OCPPCallResult(
        message_type_id=OCPPMessageType.CALLRESULT,
        unique_id=unique_id,
        payload=payload,
    )


def create_call_error(
    unique_id: str,
    error_code: OCPPErrorCode | str,
    description: str,
    details: Optional[Dict[str, Any]] = None,
) -> OCPPCallError:
    """Helper to create a well-formed OCPP 1.6-J CALLERROR frame."""
    code_val = error_code.value if isinstance(error_code, OCPPErrorCode) else str(error_code)
    return OCPPCallError(
        message_type_id=OCPPMessageType.CALLERROR,
        unique_id=unique_id or "",
        error_code=code_val,
        error_description=description,
        error_details=details or {},
    )


@dataclass
class PendingRequest:
    """Represents an in-flight OCPP CALL awaiting a CALLRESULT or CALLERROR."""
    unique_id: str
    action: str
    direction: str  # "CHARGER_TO_CSMS" or "CSMS_TO_CHARGER"
    created_at: float
    sequence_token: int
    timeout_seconds: float


class RequestTracker:
    """
    Tracks pending in-flight requests and correlates responses.
    Guards against UniqueId reuse, duplicate responses, and late/timed-out frames.
    """

    def __init__(self):
        self._pending: Dict[str, PendingRequest] = {}
        self._next_sequence: int = 1

    @property
    def pending_count(self) -> int:
        return len(self._pending)

    def register_call(
        self,
        call: OCPPCall,
        direction: str,
        timeout_seconds: float = 10.0,
        now: Optional[float] = None,
    ) -> PendingRequest:
        """Register a new outbound/forwarded CALL."""
        current_time = now if now is not None else time.monotonic()
        req = PendingRequest(
            unique_id=call.unique_id,
            action=call.action,
            direction=direction,
            created_at=current_time,
            sequence_token=self._next_sequence,
            timeout_seconds=timeout_seconds,
        )
        self._next_sequence += 1
        self._pending[call.unique_id] = req
        return req

    def match_response(
        self,
        unique_id: str,
        response_direction: str,
        now: Optional[float] = None,
    ) -> Tuple[Optional[PendingRequest], Optional[str]]:
        """
        Attempt to correlate an incoming response (CALLRESULT or CALLERROR).
        
        Returns:
            (matched_request, error_reason)
            If error_reason is None, matched_request is returned and removed from tracking.
            If error_reason is not None, matched_request is None and the response should be dropped.
        """
        current_time = now if now is not None else time.monotonic()

        if unique_id not in self._pending:
            return None, "unsolicited_or_unknown_unique_id"

        req = self._pending[unique_id]

        # Verify direction: response must come from the opposite direction of the request
        expected_response_direction = "CSMS_TO_CHARGER" if req.direction == "CHARGER_TO_CSMS" else "CHARGER_TO_CSMS"
        if response_direction != expected_response_direction:
            return None, f"direction_mismatch: expected {expected_response_direction}, got {response_direction}"

        # Check for timeout
        elapsed = current_time - req.created_at
        if elapsed > req.timeout_seconds:
            # Drop from pending and report timeout
            self._pending.pop(unique_id, None)
            return None, f"request_timed_out: elapsed {elapsed:.2f}s > {req.timeout_seconds:.2f}s"

        # Valid correlation: remove and return
        self._pending.pop(unique_id, None)
        return req, None

    def prune_expired(self, now: Optional[float] = None) -> List[PendingRequest]:
        """Prune all requests that have exceeded their timeout window."""
        current_time = now if now is not None else time.monotonic()
        expired: List[PendingRequest] = []
        for uid, req in list(self._pending.items()):
            if (current_time - req.created_at) > req.timeout_seconds:
                expired.append(req)
                self._pending.pop(uid, None)
        return expired

    def clear(self) -> List[PendingRequest]:
        """Clear and return all pending requests upon connection teardown."""
        all_reqs = list(self._pending.values())
        self._pending.clear()
        return all_reqs
