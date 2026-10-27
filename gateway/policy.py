"""
ThreatLens Deterministic OCPP 1.6-J Gateway Policy Engine (Phase 1).

Implements the three-tier ALLOW / CLAMP / BLOCK deterministic decision matrix:
- Rule R-01: Hardware Current Ceiling & Overcurrent Clamping
- Rule R-02: Rate Limiting & Command Flutter Protection (>= 5.0s interval)
- Rule R-03: State Machine & Authorization Sequence Validation
- Rule R-04: Thermal Lockout Protection (>= 45.0°C caution threshold)

Strict Zero Machine Learning constraint: 100% deterministic, rule-based branching logic.
"""

import copy
from dataclasses import dataclass, field
from enum import Enum
import logging
import time
from typing import Any, Dict, List, Optional, Tuple

from gateway.models import (
    OCPPCall,
    OCPPCallError,
    OCPPErrorCode,
    create_call_error,
)

logger = logging.getLogger("ThreatLens.Gateway.Policy")


class PolicyDecision(str, Enum):
    """Deterministic policy decision states."""
    ALLOW = "ALLOW"
    CLAMP = "CLAMP"
    BLOCK = "BLOCK"


@dataclass
class PolicyEvaluationResult:
    """Outcome of a policy evaluation against an OCPP frame."""
    decision: PolicyDecision
    rule_id: str
    reason: str
    original_limit: Optional[float] = None
    modified_limit: Optional[float] = None
    modified_payload: Optional[Dict[str, Any]] = None
    error_code: Optional[OCPPErrorCode] = None
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "decision": self.decision.value,
            "rule_id": self.rule_id,
            "reason": self.reason,
            "original_limit": self.original_limit,
            "modified_limit": self.modified_limit,
            "error_code": self.error_code.value if self.error_code else None,
            "timestamp": self.timestamp,
        }


@dataclass
class PolicyConfig:
    """Configurable parameters for deterministic gateway safety rules."""
    # Rule R-01: Current Ceiling
    current_cap_enabled: bool = True
    current_cap_value: float = 100.0        # Default safe cap in Amperes
    hardware_max_current: float = 150.0     # Hard hardware breaker limit in Amperes

    # Rule R-02: Rate Limiting
    rate_limiting_enabled: bool = True
    min_command_interval_seconds: float = 5.0  # Minimum seconds between consecutive setpoints

    # Rule R-03: Authorization & State
    auth_validation_enabled: bool = True

    # Rule R-04: Thermal Protection
    thermal_lockout_enabled: bool = True
    thermal_lockout_threshold_c: float = 45.0  # Lockout if temp >= 45.0 °C


@dataclass
class ChargerState:
    """Tracks state machine status and command history per charge point."""
    charge_point_id: str
    status: str = "Available"               # "Available", "Preparing", "Charging", "SuspendedEVSE", "Faulted"
    temperature_c: float = 25.0
    authorized_id_tag: Optional[str] = None
    last_command_timestamps: Dict[str, float] = field(default_factory=dict)
    active_transaction_id: Optional[int] = None


class GatewayPolicyEngine:
    """
    Deterministic safety evaluation engine for ThreatLens OCPP Gateway.
    Zero machine learning, 100% deterministic rules.
    """

    def __init__(self, config: Optional[PolicyConfig] = None):
        self.config = config or PolicyConfig()
        self._charger_states: Dict[str, ChargerState] = {}

    def get_or_create_state(self, charge_point_id: str) -> ChargerState:
        """Retrieve or initialize tracking state for a given charge point."""
        if charge_point_id not in self._charger_states:
            self._charger_states[charge_point_id] = ChargerState(charge_point_id=charge_point_id)
        return self._charger_states[charge_point_id]

    def set_charger_temperature(self, charge_point_id: str, temp_c: float) -> None:
        """Update simulated temperature for testing Rule R-04."""
        state = self.get_or_create_state(charge_point_id)
        state.temperature_c = temp_c

    def update_config(
        self,
        current_cap_enabled: Optional[bool] = None,
        current_cap_value: Optional[float] = None,
        rate_limiting_enabled: Optional[bool] = None,
        min_command_interval_seconds: Optional[float] = None,
        auth_validation_enabled: Optional[bool] = None,
        thermal_lockout_enabled: Optional[bool] = None,
        thermal_lockout_threshold_c: Optional[float] = None,
    ) -> None:
        """Update policy parameters dynamically."""
        if current_cap_enabled is not None:
            self.config.current_cap_enabled = current_cap_enabled
        if current_cap_value is not None:
            self.config.current_cap_value = current_cap_value
        if rate_limiting_enabled is not None:
            self.config.rate_limiting_enabled = rate_limiting_enabled
        if min_command_interval_seconds is not None:
            self.config.min_command_interval_seconds = min_command_interval_seconds
        if auth_validation_enabled is not None:
            self.config.auth_validation_enabled = auth_validation_enabled
        if thermal_lockout_enabled is not None:
            self.config.thermal_lockout_enabled = thermal_lockout_enabled
        if thermal_lockout_threshold_c is not None:
            self.config.thermal_lockout_threshold_c = thermal_lockout_threshold_c

    def evaluate_call(
        self,
        call: OCPPCall,
        direction: str,
        charge_point_id: str,
        now: Optional[float] = None,
    ) -> PolicyEvaluationResult:
        """
        Evaluate an inbound OCPP CALL frame against deterministic rules.
        
        Args:
            call: The parsed OCPP CALL frame.
            direction: "CSMS_TO_CHARGER" or "CHARGER_TO_CSMS".
            charge_point_id: Target charge point identifier.
            now: Monotonic or epoch timestamp override for reproducible testing.
            
        Returns:
            PolicyEvaluationResult (ALLOW, CLAMP, or BLOCK).
        """
        current_time = now if now is not None else time.time()
        state = self.get_or_create_state(charge_point_id)
        action = call.action
        payload = call.payload or {}

        # -----------------------------------------------------------------
        # 1. Update internal state on Charger-reported notifications
        # -----------------------------------------------------------------
        if direction == "CHARGER_TO_CSMS":
            if action == "StatusNotification":
                new_status = payload.get("status", state.status)
                state.status = new_status
                logger.debug("[%s] Updated status to %s", charge_point_id, new_status)
            elif action == "MeterValues":
                # Check if telemetry includes temperature
                meter_val = payload.get("meterValue", [])
                if isinstance(meter_val, list) and meter_val:
                    for mv in meter_val:
                        sampled = mv.get("sampledValue", [])
                        for sv in sampled:
                            if sv.get("measurand") == "Temperature":
                                with_val = sv.get("value")
                                if with_val is not None:
                                    try:
                                        state.temperature_c = float(with_val)
                                    except (ValueError, TypeError):
                                        pass
            # Charger -> CSMS calls pass through unless malformed (handled in parser)
            return PolicyEvaluationResult(
                decision=PolicyDecision.ALLOW,
                rule_id="R-00",
                reason=f"Charger telemetry/notification '{action}' permitted",
            )

        # -----------------------------------------------------------------
        # 2. Downstream commands: CSMS -> CHARGER
        # -----------------------------------------------------------------

        # RULE R-04: Thermal Lockout Protection
        if self.config.thermal_lockout_enabled and state.temperature_c >= self.config.thermal_lockout_threshold_c:
            if action in ("RemoteStartTransaction", "SetChargingProfile"):
                return PolicyEvaluationResult(
                    decision=PolicyDecision.BLOCK,
                    rule_id="R-04",
                    reason=(
                        f"Thermal Lockout Active: Charger temperature {state.temperature_c:.1f}°C "
                        f"exceeds safety threshold {self.config.thermal_lockout_threshold_c:.1f}°C"
                    ),
                    error_code=OCPPErrorCode.SecurityError,
                )

        # RULE R-03: Authorization & State Machine Validation
        if action == "RemoteStartTransaction" and self.config.auth_validation_enabled:
            id_tag = str(payload.get("idTag", "")).strip().upper()
            # Explicit rogue tokens or empty tokens blocked
            if not id_tag or "UNAUTH" in id_tag or "ROGUE" in id_tag or "EXPIRED" in id_tag or "INVALID" in id_tag:
                return PolicyEvaluationResult(
                    decision=PolicyDecision.BLOCK,
                    rule_id="R-03",
                    reason=f"Unauthorized transaction request: idTag '{id_tag}' rejected by access policy",
                    error_code=OCPPErrorCode.SecurityError,
                )
            if state.status in ("Faulted", "SuspendedEVSE"):
                return PolicyEvaluationResult(
                    decision=PolicyDecision.BLOCK,
                    rule_id="R-03",
                    reason=f"Cannot start transaction: Charger is in non-operable status '{state.status}'",
                    error_code=OCPPErrorCode.SecurityError,
                )
            state.authorized_id_tag = id_tag

        # RULE R-02: Rate Limiting & Command Flutter
        if action == "SetChargingProfile" and self.config.rate_limiting_enabled:
            last_time = state.last_command_timestamps.get("SetChargingProfile")
            if last_time is not None:
                elapsed = current_time - last_time
                if elapsed < self.config.min_command_interval_seconds:
                    return PolicyEvaluationResult(
                        decision=PolicyDecision.BLOCK,
                        rule_id="R-02",
                        reason=(
                            f"Command Rate Limit Exceeded: Interval between setpoints was {elapsed:.2f}s "
                            f"(minimum required: {self.config.min_command_interval_seconds:.1f}s)"
                        ),
                        error_code=OCPPErrorCode.OccurenceConstraintViolation,
                    )

        # RULE R-01: Hardware Current Ceiling & Overcurrent Clamping
        if action == "SetChargingProfile":
            limit_val, clamp_path = self._extract_current_limit(payload)
            if limit_val is not None:
                # Active safe cap is min(configured_cap, hardware_max)
                active_cap = min(self.config.current_cap_value, self.config.hardware_max_current) \
                    if self.config.current_cap_enabled else self.config.hardware_max_current

                if limit_val > active_cap:
                    clamped_payload = self._apply_clamped_limit(payload, clamp_path, active_cap)
                    # Update rate limit tracker on successful clamped command
                    state.last_command_timestamps["SetChargingProfile"] = current_time
                    return PolicyEvaluationResult(
                        decision=PolicyDecision.CLAMP,
                        rule_id="R-01",
                        reason=(
                            f"Requested current {limit_val:.1f}A exceeds safe ceiling {active_cap:.1f}A; "
                            f"clamped setpoint to {active_cap:.1f}A"
                        ),
                        original_limit=limit_val,
                        modified_limit=active_cap,
                        modified_payload=clamped_payload,
                    )

            # Record timestamp for allowed SetChargingProfile
            state.last_command_timestamps["SetChargingProfile"] = current_time

        # Update last command time for generic commands
        state.last_command_timestamps[action] = current_time

        # DEFAULT: ALLOW
        return PolicyEvaluationResult(
            decision=PolicyDecision.ALLOW,
            rule_id="R-00",
            reason=f"Action '{action}' complies with all active safety policies",
        )

    def _extract_current_limit(self, payload: Dict[str, Any]) -> Tuple[Optional[float], Optional[str]]:
        """
        Extracts requested charging current from SetChargingProfile payload.
        Supports both full canonical OCPP 1.6-J structures and flat mock payloads.
        
        Returns:
            (limit_val, path_type)
        """
        # 1. Flat simplified payload {"limit": 180.0}
        if "limit" in payload:
            try:
                return float(payload["limit"]), "flat"
            except (ValueError, TypeError):
                pass

        # 2. Canonical OCPP 1.6-J structure
        # payload -> csChargingProfiles -> chargingSchedule -> chargingSchedulePeriod[0] -> limit
        profile = payload.get("csChargingProfiles")
        if isinstance(profile, dict):
            schedule = profile.get("chargingSchedule")
            if isinstance(schedule, dict):
                periods = schedule.get("chargingSchedulePeriod")
                if isinstance(periods, list) and len(periods) > 0 and isinstance(periods[0], dict):
                    limit_raw = periods[0].get("limit")
                    if limit_raw is not None:
                        try:
                            return float(limit_raw), "canonical"
                        except (ValueError, TypeError):
                            pass

        return None, None

    def _apply_clamped_limit(
        self,
        payload: Dict[str, Any],
        path_type: Optional[str],
        clamped_value: float,
    ) -> Dict[str, Any]:
        """Deep copy payload and update limit to clamped value."""
        modified = copy.deepcopy(payload)
        if path_type == "flat":
            modified["limit"] = clamped_value
        elif path_type == "canonical":
            try:
                modified["csChargingProfiles"]["chargingSchedule"]["chargingSchedulePeriod"][0]["limit"] = clamped_value
            except (KeyError, IndexError, TypeError):
                modified["limit"] = clamped_value
        else:
            modified["limit"] = clamped_value
        return modified
