"""
Confidence Breakdown and Impact Severity Services (Features F26, F27).
Computes multi-factor causal confidence breakdowns with documented weighting rationale,
and multidimensional impact severity scores independent of causal attribution.
"""

from typing import Dict, Any, List, Optional
from backend.app.schemas.analysis import (
    ConfidenceBreakdown,
    ImpactSeverity,
    SeverityLevel,
)
from backend.app.schemas.telemetry import TelemetryTimeSlice


class ConfidenceAndSeverityEngine:

    @classmethod
    def compute_confidence_breakdown(
        cls,
        path_valid: bool,
        measured_delay: float,
        expected_window: tuple,
        physics_consistency_score: float,
        counterfactual_delta: float,
        is_authorized: bool,
        has_alternative_cause: bool = False
    ) -> ConfidenceBreakdown:
        """
        Calculates multi-factor confidence breakdown:
        - Path validity (0.25)
        - Timing fit (0.20)
        - Physics consistency (0.20)
        - Counterfactual effect (0.20)
        - Command provenance (0.15)
        - Alternative explanation penalty (up to -0.15)
        """
        # 1. Path validity
        score_path = 1.0 if path_valid else 0.2

        # 2. Timing fit: check if delay is within [min_d, max_d]
        min_d, max_d = expected_window
        if min_d <= measured_delay <= max_d:
            score_timing = 1.0
        elif measured_delay < min_d:
            score_timing = max(0.2, 1.0 - (min_d - measured_delay) / 5.0)
        else:
            score_timing = max(0.2, 1.0 - (measured_delay - max_d) / 10.0)

        # 3. Physics consistency
        score_physics = max(0.0, min(1.0, physics_consistency_score))

        # 4. Counterfactual score: higher when effect disappeared or decreased strongly
        if counterfactual_delta > 10.0:
            score_cf = 1.0
        elif counterfactual_delta > 2.0:
            score_cf = 0.8
        elif counterfactual_delta > 0.0:
            score_cf = 0.5
        else:
            score_cf = 0.2

        # 5. Provenance score: unauthorized or spoofed commands yield high attribution confidence to malicious event
        score_provenance = 0.95 if not is_authorized else 0.70

        # 6. Alternative explanation penalty
        penalty = -0.12 if has_alternative_cause else 0.0

        # Weighted sum
        composite = (
            (score_path * 0.25) +
            (score_timing * 0.20) +
            (score_physics * 0.20) +
            (score_cf * 0.20) +
            (score_provenance * 0.15) +
            penalty
        )
        final_score = round(max(0.0, min(1.0, composite)), 3)

        if final_score >= 0.75:
            level = "High (>=0.75)"
        elif final_score >= 0.50:
            level = "Medium (0.50-0.75)"
        else:
            level = "Low (<0.50)"

        notes = (
            f"Weights: Path (25%), Timing (20%), Physics (20%), Counterfactual (20%), Provenance (15%). "
            f"Alternative penalty: {penalty}. Score reflects engineering testbed heuristics, not calibrated probabilities."
        )

        return ConfidenceBreakdown(
            path_validity_score=round(score_path, 2),
            timing_fit_score=round(score_timing, 2),
            physics_consistency_score=round(score_physics, 2),
            counterfactual_score=round(score_cf, 2),
            command_provenance_score=round(score_provenance, 2),
            alternative_explanation_penalty=round(penalty, 2),
            final_score=final_score,
            confidence_level=level,
            scoring_notes=notes
        )

    @classmethod
    def evaluate_impact_severity(
        cls,
        telemetry: List[TelemetryTimeSlice],
        critical_temp_threshold: float = 70.0,
        warning_temp_threshold: float = 60.0
    ) -> ImpactSeverity:
        """
        Evaluates physical impact severity based on telemetry states, independent of causal link.
        """
        if not telemetry:
            return ImpactSeverity(
                severity_level=SeverityLevel.LOW,
                peak_current_observed=0.0,
                peak_temp_observed=25.0,
                distance_to_critical_temp_c=45.0,
                rate_of_temp_rise_c_per_min=0.0,
                abnormal_duration_seconds=0.0,
                components_affected_count=0,
                protection_tripped=False,
                explanation="No telemetry available to evaluate."
            )

        peak_current = max((s.charging_current for s in telemetry), default=0.0)
        peak_temp = max((s.battery_temperature for s in telemetry), default=25.0)
        dist_critical = max(0.0, critical_temp_threshold - peak_temp)

        # Rate of temperature rise (°C / minute)
        temps = [s.battery_temperature for s in telemetry]
        dt_total = max(1.0, float(len(telemetry) - 1))
        temp_delta = temps[-1] - temps[0]
        rate_c_per_min = round((temp_delta / dt_total) * 60.0, 2)

        # Count abnormal duration (temp >= warning threshold or current > 120A)
        abnormal_slices = [s for s in telemetry if s.battery_temperature >= warning_temp_threshold or s.charging_current >= 120.0]
        abnormal_duration = float(len(abnormal_slices))

        # Check protection trip
        protection_tripped = any(s.charger_state == "FAULT" for s in telemetry)

        # Components affected
        components = set()
        if peak_current > 0.0:
            components.add("evse_controller")
            components.add("power_converter")
        if peak_temp > 35.0:
            components.add("battery_pack")
        if any(s.cooling_power > 500 for s in telemetry):
            components.add("cooling_system")
        if protection_tripped:
            components.add("hardware_safety_breaker")

        # Determine severity level
        if peak_temp >= critical_temp_threshold or protection_tripped:
            level = SeverityLevel.CRITICAL
            explanation = f"Critical threshold ({critical_temp_threshold}°C) reached or protective circuit breaker tripped."
        elif peak_temp >= warning_temp_threshold or peak_current >= 135.0:
            level = SeverityLevel.HIGH
            explanation = f"High thermal/electrical stress: peak {peak_temp:.1f}°C, peak current {peak_current:.1f}A."
        elif peak_temp >= 45.0 or peak_current >= 80.0:
            level = SeverityLevel.MEDIUM
            explanation = f"Moderate stress operating above standard continuous rating ({peak_temp:.1f}°C, {peak_current:.1f}A)."
        else:
            level = SeverityLevel.LOW
            explanation = f"Nominal operating parameters maintained throughout test run."

        return ImpactSeverity(
            severity_level=level,
            peak_current_observed=round(peak_current, 1),
            peak_temp_observed=round(peak_temp, 1),
            distance_to_critical_temp_c=round(dist_critical, 1),
            rate_of_temp_rise_c_per_min=rate_c_per_min,
            abnormal_duration_seconds=abnormal_duration,
            components_affected_count=len(components),
            protection_tripped=protection_tripped,
            explanation=explanation
        )
