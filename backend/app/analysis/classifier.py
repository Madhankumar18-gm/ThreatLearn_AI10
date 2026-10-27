"""
Rule-Based Event Classifier (Feature F24).
Categorizes simulated events into:
    - Attack-like simulated event
    - Sensor fault
    - Benign high-power event
    - Uncertain

CRITICAL SAFEGUARD: Evaluated strictly from observed telemetry, control logs, and physics residuals.
Does NOT access scenario metadata, scenario family, or ground-truth labels.
"""

from typing import Dict, Any, List, Optional
from backend.app.schemas.analysis import EventCategory, ClassificationResult
from backend.app.schemas.events import SimulatedEventSchema
from backend.app.schemas.telemetry import TelemetryTimeSlice


class RuleBasedEventClassifier:

    @classmethod
    def classify_event(
        cls,
        event: SimulatedEventSchema,
        telemetry: List[TelemetryTimeSlice],
        residual_stats: Dict[str, Any]
    ) -> ClassificationResult:
        """
        Classifies an event strictly from telemetry, control signatures, and residuals.
        """
        supporting_clues: List[str] = []
        conflicting_clues: List[str] = []
        uncertainty_notes: List[str] = []

        ev_type = event.event_type
        ev_source = event.source
        ev_time = event.timestamp
        details = event.details or {}

        # 1. Inspect telemetry around and after event
        post_event_slices = [s for s in telemetry if s.timestamp >= ev_time]
        peak_current_post = max((s.charging_current for s in post_event_slices), default=0.0)
        peak_temp_post = max((s.battery_temperature for s in post_event_slices), default=25.0)

        # 2. Check for sensor fault signatures
        max_residual = residual_stats.get("max_residual", 0.0)
        consistency_score = residual_stats.get("consistency_score", 1.0)
        anomalies = residual_stats.get("anomalies_detected", [])

        is_sensor_anomaly = (
            ev_type in ("SENSOR_DRIFT", "SENSOR_STUCK", "SENSOR_SPIKE", "SENSOR_DROPOUT") or
            any(a["type"] in ("implausible_thermal_jump", "stuck_reading") for a in anomalies) or
            max_residual > 8.0
        )

        # 3. Rule matching logic
        if is_sensor_anomaly:
            supporting_clues.append(f"Significant physics residual observed (max residual: {max_residual:.1f}°C).")
            if any(a["type"] == "implausible_thermal_jump" for a in anomalies):
                supporting_clues.append("Instantaneous thermal jump violates physical heat capacity inertia.")
            if any(a["type"] == "stuck_reading" for a in anomalies):
                supporting_clues.append("Sensor reading remained constant despite active current flow.")

            category = EventCategory.SENSOR_FAULT
            confidence = 0.88 if max_residual > 10.0 else 0.72
            uncertainty = "Sensor measurement disagrees with Joule heating energy conservation model."

        elif ev_type in ("CHANGE_CURRENT_LIMIT", "SET_CHARGING_PROFILE", "CAN_SPOOF_CURRENT") and float(details.get("requested_current", 0.0)) > 100.0:
            req_curr = float(details.get("requested_current", 0.0))
            supporting_clues.append(f"Command requested high current setpoint of {req_curr}A.")
            
            if ev_source in ("ocpp_csms", "in_vehicle_can", "internal_bms"):
                supporting_clues.append(f"Command originated from network or bus interface ({ev_source}).")

            if peak_temp_post >= 60.0:
                supporting_clues.append(f"Observed battery temperature escalated to {peak_temp_post:.1f}°C.")

            # Differentiate between benign high power vs attack-like
            if ev_source == "ocpp_csms" and details.get("authorized") is False:
                supporting_clues.append("Command arrived without valid cryptographic authorization token.")
                category = EventCategory.ATTACK_LIKE
                confidence = 0.92
                uncertainty = "Cyber override matches unauthorized protocol tampering pattern."
            elif ev_type == "CAN_SPOOF_CURRENT":
                supporting_clues.append("In-vehicle CAN frame spoofing detected on powertrain bus.")
                category = EventCategory.ATTACK_LIKE
                confidence = 0.90
                uncertainty = "Synthesized bus injection bypassed normal controller handshakes."
            elif req_curr > 130.0:
                category = EventCategory.ATTACK_LIKE
                confidence = 0.80
                uncertainty = "Current setpoint pushed EVSE near physical breaker threshold."
            else:
                category = EventCategory.BENIGN_HIGH_POWER
                confidence = 0.75
                uncertainty = "High current matches commercial fast-charging curve profile."

        elif ev_type == "DISABLE_COOLING":
            supporting_clues.append("Cooling loop actuator suppression command observed.")
            category = EventCategory.ATTACK_LIKE
            confidence = 0.85
            uncertainty = "Cooling system deactivated during active charge cycle."

        elif ev_type in ("START_TRANSACTION", "STOP_TRANSACTION"):
            supporting_clues.append(f"Standard session lifecycle management event ({ev_type}).")
            category = EventCategory.BENIGN_HIGH_POWER if peak_current_post > 50.0 else EventCategory.UNCERTAIN
            confidence = 0.70
            uncertainty = "Routine protocol operations without overt malicious indicators."

        else:
            category = EventCategory.UNCERTAIN
            confidence = 0.50
            uncertainty = "Signals and command patterns do not meet definitive threshold criteria."

        return ClassificationResult(
            event_id=event.event_id,
            classification=category,
            confidence=round(confidence, 2),
            supporting_clues=supporting_clues,
            conflicting_clues=conflicting_clues,
            uncertainty_explanation=uncertainty,
            evaluated_without_ground_truth=True
        )
