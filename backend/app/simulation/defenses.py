"""
Simulated Cyber-Physical Mitigations & Defense Engine (Features F39, F40).
Applies active simulated defenses to the EV charging digital twin during simulation steps:
1. Command authorization / signature check
2. Allowed-command whitelist
3. Charging current software ceiling cap
4. Command rate limiting
5. Sensor cross-checking against digital twin prediction
6. Thermal protection lockout
"""

from typing import List, Dict, Any, Optional, Tuple
from backend.app.schemas.defense import DefenseConfiguration, DefenseIntervention
from backend.app.schemas.events import SimulatedEventSchema


class DefenseEngine:
    def __init__(self, config: Optional[DefenseConfiguration] = None):
        self.config = config or DefenseConfiguration()
        self.interventions: List[DefenseIntervention] = []
        self.last_command_time: Dict[str, float] = {}
        self.is_locked_out = False

    def inspect_event(self, event: SimulatedEventSchema, current_time: float) -> Tuple[bool, Optional[str]]:
        """
        Evaluates incoming command against active cyber mitigations.
        Returns: (is_allowed, denial_reason)
        """
        if self.is_locked_out:
            intervention = DefenseIntervention(
                timestamp=current_time,
                mitigation_name="Thermal Protection Lockout",
                target_event_id=event.event_id,
                action_taken="BLOCKED",
                reason="System in persistent thermal lockout state",
                details={"event_type": event.event_type}
            )
            self.interventions.append(intervention)
            return False, "Thermal protection lockout active"

        # Mitigation 1: Authorization validation
        if self.config.auth_validation_enabled:
            if event.auth_status in ("unauthorized", "spoofed", "bypassed"):
                intervention = DefenseIntervention(
                    timestamp=current_time,
                    mitigation_name="Command Authorization Check",
                    target_event_id=event.event_id,
                    action_taken="BLOCKED",
                    reason=f"Rejected command with {event.auth_status} authorization",
                    details={"auth_status": event.auth_status, "event_type": event.event_type}
                )
                self.interventions.append(intervention)
                return False, f"Unauthorized command rejected ({event.auth_status})"

        # Mitigation 2: Allowed-command whitelist
        if self.config.command_whitelist_enabled:
            if event.event_type not in self.config.allowed_commands:
                intervention = DefenseIntervention(
                    timestamp=current_time,
                    mitigation_name="Allowed-Command Whitelist",
                    target_event_id=event.event_id,
                    action_taken="BLOCKED",
                    reason=f"Command '{event.event_type}' not in whitelist",
                    details={"allowed": self.config.allowed_commands}
                )
                self.interventions.append(intervention)
                return False, f"Command '{event.event_type}' not permitted by whitelist"

        # Mitigation 4: Command rate limiting
        if self.config.rate_limiting_enabled:
            last_time = self.last_command_time.get(event.event_type)
            if last_time is not None and (current_time - last_time) < self.config.min_interval_seconds:
                intervention = DefenseIntervention(
                    timestamp=current_time,
                    mitigation_name="Command Rate Limiting",
                    target_event_id=event.event_id,
                    action_taken="BLOCKED",
                    reason=f"Rate limit exceeded: only {current_time - last_time:.1f}s since last {event.event_type}",
                    details={"min_interval": self.config.min_interval_seconds}
                )
                self.interventions.append(intervention)
                return False, "Rate limit exceeded"
            self.last_command_time[event.event_type] = current_time

        return True, None

    def apply_current_cap(self, requested_current: float, current_time: float) -> float:
        """Mitigation 3: Clamps requested current to software cap ceiling."""
        if self.config.current_cap_enabled and requested_current > self.config.current_cap_value:
            intervention = DefenseIntervention(
                timestamp=current_time,
                mitigation_name="Charging Current Cap",
                action_taken="CAPPED",
                reason=f"Clamped requested current from {requested_current}A to cap ceiling of {self.config.current_cap_value}A",
                details={"original": requested_current, "capped": self.config.current_cap_value}
            )
            self.interventions.append(intervention)
            return self.config.current_cap_value
        return requested_current

    def inspect_sensor(self, reported_temp: float, physical_temp: float, current_time: float) -> bool:
        """
        Mitigation 5: Sensor cross-checking against digital twin prediction.
        Returns: True if anomaly detected and flagged.
        """
        if self.config.sensor_crosscheck_enabled:
            divergence = abs(reported_temp - physical_temp)
            if divergence > self.config.crosscheck_tolerance_c:
                intervention = DefenseIntervention(
                    timestamp=current_time,
                    mitigation_name="Sensor Cross-Checking",
                    action_taken="FLAGGED",
                    reason=f"Sensor divergence of {divergence:.1f}°C exceeds tolerance of {self.config.crosscheck_tolerance_c}°C",
                    details={"reported": reported_temp, "physical": physical_temp, "divergence": divergence}
                )
                self.interventions.append(intervention)
                return True
        return False

    def inspect_thermal_lockout(self, physical_temp: float, current_time: float) -> bool:
        """
        Mitigation 6: Thermal protection lockout.
        Returns: True if lockout triggered.
        """
        if self.config.thermal_lockout_enabled and not self.is_locked_out:
            if physical_temp >= self.config.lockout_threshold_c:
                self.is_locked_out = True
                intervention = DefenseIntervention(
                    timestamp=current_time,
                    mitigation_name="Thermal Protection Lockout",
                    action_taken="LOCKOUT",
                    reason=f"Pack temperature {physical_temp:.1f}°C reached lockout threshold {self.config.lockout_threshold_c}°C",
                    details={"threshold": self.config.lockout_threshold_c}
                )
                self.interventions.append(intervention)
                return True
        return self.is_locked_out
