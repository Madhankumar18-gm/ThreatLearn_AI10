"""
Explainable Rule-Based Correlation Engine (Features F21, F29).
Evaluates candidate event-to-impact links using:
1. Graph dependency path existence
2. Signal-event physical compatibility
3. Plausible physical time delays
4. Exceeding baseline noise margins
5. Grounded evidence labeling: Observed, Inferred, Uncertain.
Temporal order alone is never treated as proof of causation.
"""

import uuid
from typing import List, Dict, Any, Optional, Tuple
from backend.app.schemas.simulation import SimulationRunResponse
from backend.app.schemas.events import SimulatedEventSchema
from backend.app.schemas.analysis import CorrelationLink, EvidenceLabel
from backend.app.analysis.dependency_graph import dependency_graph


# Signal compatibility matrix: which event types can physically cause shifts in which signals
COMPATIBILITY_MATRIX: Dict[str, List[str]] = {
    "charging_current": [
        "START_TRANSACTION", "STOP_TRANSACTION", "CHANGE_CURRENT_LIMIT",
        "SET_CHARGING_PROFILE", "BMS_OVERRIDE_ATTEMPT", "EMERGENCY_STOP", "FIRMWARE_UPDATE",
        "CAN_SPOOF_CURRENT"
    ],
    "battery_temperature": [
        "CHANGE_CURRENT_LIMIT", "SET_CHARGING_PROFILE", "BMS_OVERRIDE_ATTEMPT",
        "COOLING_OVERRIDE", "DISABLE_COOLING", "FIRMWARE_UPDATE", "EMERGENCY_STOP",
        "CAN_SPOOF_CURRENT", "CAN_SPOOF_TEMPERATURE",
        "SENSOR_DRIFT", "SENSOR_STUCK", "SENSOR_SPIKE", "SENSOR_DROPOUT"
    ],
    "battery_voltage": [
        "START_TRANSACTION", "STOP_TRANSACTION", "CHANGE_CURRENT_LIMIT",
        "BMS_OVERRIDE_ATTEMPT", "EMERGENCY_STOP", "CAN_SPOOF_CURRENT"
    ],
    "state_of_charge": [
        "START_TRANSACTION", "CHANGE_CURRENT_LIMIT", "BMS_OVERRIDE_ATTEMPT", "CAN_SPOOF_CURRENT"
    ],
    "grid_load": [
        "START_TRANSACTION", "STOP_TRANSACTION", "CHANGE_CURRENT_LIMIT",
        "BMS_OVERRIDE_ATTEMPT", "GRID_LIMIT_UPDATE", "EMERGENCY_STOP", "CAN_SPOOF_CURRENT"
    ],
    "sensor_temperature": [
        "SENSOR_INJECT_FAULT", "COOLING_OVERRIDE", "DISABLE_COOLING", "CHANGE_CURRENT_LIMIT",
        "CAN_SPOOF_TEMPERATURE", "SENSOR_DRIFT", "SENSOR_STUCK", "SENSOR_SPIKE", "SENSOR_DROPOUT"
    ]
}

# Plausible physical response delays (min, max in seconds)
PLAUSIBLE_DELAYS: Dict[str, Tuple[float, float]] = {
    "charging_current": (0.0, 4.0),
    "battery_voltage": (0.0, 4.0),
    "grid_load": (0.0, 4.0),
    "sensor_temperature": (0.0, 2.5),
    "battery_temperature": (2.0, 45.0),  # Thermal inertia requires seconds to accumulate Joule heat
    "state_of_charge": (5.0, 60.0)
}

# Minimum signal change required to exceed noise margin
MIN_NOISE_MARGINS: Dict[str, float] = {
    "charging_current": 5.0,     # Amperes
    "battery_temperature": 0.8,  # °C
    "battery_voltage": 2.0,      # Volts
    "grid_load": 2.0,            # kW
    "sensor_temperature": 1.5,   # °C
    "state_of_charge": 0.1       # %
}

SIGNAL_UNITS: Dict[str, str] = {
    "charging_current": "A",
    "battery_temperature": "°C",
    "battery_voltage": "V",
    "grid_load": "kW",
    "sensor_temperature": "°C",
    "state_of_charge": "%"
}


class CorrelationEngine:

    @staticmethod
    def analyze_run(run: SimulationRunResponse) -> List[CorrelationLink]:
        """
        Evaluates all simulated events against physical telemetry changes.
        Returns validated, explainable correlation links with evidence labels.
        """
        links: List[CorrelationLink] = []
        telemetry = run.telemetry
        if not telemetry or len(telemetry) < 2:
            return links

        # Build quick time-indexed telemetry map
        t_steps = {slice_item.timestamp: slice_item for slice_item in telemetry}
        sorted_times = sorted(t_steps.keys())

        # Evaluate each event
        for event in run.events:
            event_id = event.event_id
            ev_type = event.event_type
            t_event = event.timestamp
            source_comp = event.component_id

            # Pre-event baseline slice (1 second before or at event)
            t_pre = max(0.0, t_event - 1.0)
            baseline_slice = t_steps.get(t_pre, telemetry[0])

            # Check candidate physical signals
            for signal_name, compatible_events in COMPATIBILITY_MATRIX.items():
                if ev_type not in compatible_events:
                    continue  # Rule 2 check: Incompatible physical channel

                # Rule 1: Check dependency graph path
                if not dependency_graph.has_dependency_path(source_comp, signal_name):
                    continue  # Rule 1 failed: No directed dependency path

                path = dependency_graph.find_shortest_path(source_comp, signal_name) or [source_comp, signal_name]

                # Rule 3 & 4: Evaluate physical delay and magnitude change
                delay_min, delay_max = PLAUSIBLE_DELAYS.get(signal_name, (0.0, 30.0))
                min_margin = MIN_NOISE_MARGINS.get(signal_name, 1.0)

                # Search within plausible window [t_event + delay_min, t_event + delay_max]
                window_times = [
                    t for t in sorted_times
                    if (t_event + delay_min) <= t <= min(run.duration_seconds, t_event + delay_max)
                ]
                if not window_times:
                    continue

                # Measure max absolute change relative to baseline
                baseline_val = getattr(baseline_slice, signal_name, None)
                if baseline_val is None:
                    continue

                best_delta = 0.0
                best_t = window_times[0]
                for t in window_times:
                    val = getattr(t_steps[t], signal_name, 0.0)
                    delta = val - baseline_val
                    if abs(delta) > abs(best_delta):
                        best_delta = delta
                        best_t = t

                observed_magnitude = abs(best_delta)

                # Rule 4: Must exceed noise threshold
                if observed_magnitude < min_margin:
                    continue

                measured_delay = round(best_t - t_event, 2)
                rules_matched = [
                    f"R1: Valid dependency path verified ({' -> '.join(path)})",
                    f"R2: Event '{ev_type}' is physically compatible with signal '{signal_name}'",
                    f"R3: Measured delay ({measured_delay}s) within plausible window [{delay_min}s - {delay_max}s]",
                    f"R4: Signal delta ({observed_magnitude:.2f}) exceeds noise floor threshold ({min_margin})"
                ]

                # Evidence Label determination (F29):
                # Observed: direct event and telemetry points
                # Inferred: strong correlation through verified physical causal path
                # Uncertain: benign, noisy, or ambiguous cases
                is_unauthorized = event.auth_status in ("unauthorized", "spoofed", "bypassed")
                is_sensor_fault = event.event_type == "SENSOR_INJECT_FAULT"

                if is_unauthorized:
                    confidence = 0.88 if observed_magnitude > (min_margin * 2.0) else 0.72
                    evidence_label = EvidenceLabel.INFERRED
                    explanation = (
                        f"Unauthorized event '{ev_type}' from '{event.source}' transmitted across path "
                        f"[{' -> '.join(path)}], driving an observed physical change of {best_delta:+.2f} "
                        f"{SIGNAL_UNITS.get(signal_name, '')} after {measured_delay}s."
                    )
                    uncertainty_notes = (
                        "Correlation is supported by model physics and dependency path. "
                        "Confirm causality via counterfactual replay to rule out coincident background conditions."
                    )
                elif is_sensor_fault:
                    confidence = 0.90
                    evidence_label = EvidenceLabel.OBSERVED
                    explanation = (
                        f"Sensor fault event '{ev_type}' directly altered reporting on signal '{signal_name}' "
                        f"by {best_delta:+.2f} {SIGNAL_UNITS.get(signal_name, '')} without modifying physical battery energy delivery."
                    )
                    uncertainty_notes = "Sensor-level corruption, not an actuator or power-electronic attack."
                else:
                    # Authorized normal or benign operation
                    confidence = 0.65
                    evidence_label = EvidenceLabel.UNCERTAIN
                    explanation = (
                        f"Authorized command '{ev_type}' naturally caused operational change of "
                        f"{best_delta:+.2f} {SIGNAL_UNITS.get(signal_name, '')} as part of designed charging profile."
                    )
                    uncertainty_notes = (
                        "Classified as normal system actuation. Temporal correlation exists, but no unauthorized cyber breach is indicated."
                    )

                # Tier 2 Enrichments
                from backend.app.analysis.confidence_severity import ConfidenceAndSeverityEngine
                from backend.app.analysis.consistency_checker import PhysicsConsistencyChecker
                from backend.app.analysis.classifier import RuleBasedEventClassifier

                residual_stats = PhysicsConsistencyChecker.evaluate_telemetry(run.telemetry)
                impact_sev = ConfidenceAndSeverityEngine.evaluate_impact_severity(run.telemetry)
                
                # Construct synthetic event schema for classifier
                synthetic_ev = SimulatedEventSchema(
                    event_id=event.event_id,
                    timestamp=event.timestamp,
                    layer=getattr(event, "layer", "cyber_protocol"),
                    component_id=getattr(event, "component_id", source_comp),
                    event_type=event.event_type,
                    source=event.source,
                    auth_status=getattr(event, "auth_status", "authorized"),
                    description=getattr(event, "description", None),
                    details=event.details or {}
                )
                classification_res = RuleBasedEventClassifier.classify_event(synthetic_ev, run.telemetry, residual_stats)

                # Confidence breakdown
                conf_breakdown = ConfidenceAndSeverityEngine.compute_confidence_breakdown(
                    path_valid=True,
                    measured_delay=measured_delay,
                    expected_window=(delay_min, delay_max),
                    physics_consistency_score=residual_stats.get("consistency_score", 1.0),
                    counterfactual_delta=observed_magnitude,
                    is_authorized=not is_unauthorized,
                    has_alternative_cause=(evidence_label == EvidenceLabel.UNCERTAIN)
                )

                link = CorrelationLink(
                    link_id=f"LNK-{uuid.uuid4().hex[:6].upper()}",
                    event_id=event_id,
                    event_type=ev_type,
                    source=event.source,
                    target_signal=signal_name,
                    target_component=path[-1] if path else source_comp,
                    dependency_path=path,
                    time_delay=measured_delay,
                    observed_change=round(best_delta, 2),
                    change_unit=SIGNAL_UNITS.get(signal_name, ""),
                    confidence_score=round(conf_breakdown.final_score, 2),
                    evidence_label=evidence_label,
                    rules_matched=rules_matched,
                    explanation=explanation,
                    uncertainty_notes=uncertainty_notes,
                    confidence_breakdown=conf_breakdown,
                    impact_severity=impact_sev,
                    event_classification=classification_res,
                    aligned_time_delay=measured_delay
                )
                links.append(link)

        return links

    @classmethod
    def correlate_events(cls, scenario: Any, run: SimulationRunResponse) -> Tuple[List[CorrelationLink], Dict[str, Any]]:
        """
        Convenience wrapper returning correlation links and physics residual analysis.
        """
        links = cls.analyze_run(run)
        from backend.app.analysis.consistency_checker import PhysicsConsistencyChecker
        residuals = PhysicsConsistencyChecker.evaluate_telemetry(run.telemetry)
        return links, residuals

