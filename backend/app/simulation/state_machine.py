"""
EV Charger State Machine (Feature F06).
Implements states: Idle, Authorized, Charging, Fault, with limit enforcement and safety trips.
"""

from enum import Enum
from typing import Optional, Tuple


class ChargerState(str, Enum):
    IDLE = "IDLE"
    AUTHORIZED = "AUTHORIZED"
    CHARGING = "CHARGING"
    FAULT = "FAULT"


class EVChargerStateMachine:
    def __init__(self, hardware_limit_a: float = 150.0):
        self.state: ChargerState = ChargerState.IDLE
        self.hardware_limit_a: float = hardware_limit_a
        self.requested_current_a: float = 0.0
        self.bms_limit_a: float = 150.0
        self.fault_reason: Optional[str] = None
        self.bms_override_active: bool = False

    def authorize(self) -> bool:
        """Transitions IDLE -> AUTHORIZED upon user/CSMS authorization."""
        if self.state == ChargerState.IDLE:
            self.state = ChargerState.AUTHORIZED
            return True
        return False

    def start_charging(self, requested_current_a: float) -> bool:
        """Transitions AUTHORIZED -> CHARGING when cable is locked and ready."""
        if self.state in (ChargerState.AUTHORIZED, ChargerState.IDLE):
            self.state = ChargerState.CHARGING
            self.requested_current_a = max(0.0, requested_current_a)
            return True
        return False

    def stop_charging(self, reason: str = "User completed") -> bool:
        """Transitions CHARGING -> IDLE."""
        if self.state == ChargerState.CHARGING:
            self.state = ChargerState.IDLE
            self.requested_current_a = 0.0
            return True
        return False

    def trigger_fault(self, reason: str) -> None:
        """Transitions any state -> FAULT upon safety trip or hardware error."""
        self.state = ChargerState.FAULT
        self.fault_reason = reason
        self.requested_current_a = 0.0

    def reset_fault(self) -> bool:
        """Recovers from FAULT -> IDLE."""
        if self.state == ChargerState.FAULT:
            self.state = ChargerState.IDLE
            self.fault_reason = None
            self.bms_override_active = False
            return True
        return False

    def set_requested_current(self, current_a: float) -> None:
        if self.state == ChargerState.CHARGING:
            self.requested_current_a = max(0.0, current_a)

    def set_bms_limit(self, limit_a: float) -> None:
        self.bms_limit_a = max(0.0, limit_a)

    def set_bms_override(self, override: bool) -> None:
        self.bms_override_active = override

    def compute_actual_current(self) -> Tuple[float, Optional[str]]:
        """
        Calculates physical current output respecting limits.
        Actual current = min(I_req, I_hardware, I_bms) unless bms_override_active is forced.
        """
        if self.state != ChargerState.CHARGING:
            return 0.0, None

        limit_source = "requested"
        target_current = self.requested_current_a

        if not self.bms_override_active:
            # Respect BMS negotiation limit
            if target_current > self.bms_limit_a:
                target_current = self.bms_limit_a
                limit_source = "bms_limit"

        # Hardware physical capability limit is absolute
        if target_current > self.hardware_limit_a:
            target_current = self.hardware_limit_a
            limit_source = "hardware_limit"

        return target_current, limit_source
