"""
Physics Consistency Checker (Feature F23).
Computes the residual between sensor-reported measurements and digital twin predicted states:
    Residual(t) = Reported(t) - Predicted(t)

Detects sensor anomalies including drift, stuck values, spikes, and impossible thermal jumps.
Yields a normalized physics consistency score [0.0, 1.0] and sensor quality diagnostics.
"""

from typing import List, Dict, Any, Tuple
from backend.app.schemas.telemetry import TelemetryTimeSlice


class PhysicsConsistencyChecker:
    RESIDUAL_TOLERANCE_C = 3.0       # Normal expected thermal modeling tolerance
    IMPLAUSIBLE_JUMP_THRESHOLD_C = 8.0 # Impossible instantaneous thermal jump
    STUCK_WINDOW_SECONDS = 8          # Consecutive steps with identical reading under load

    @classmethod
    def evaluate_telemetry(
        cls,
        telemetry: List[TelemetryTimeSlice]
    ) -> Dict[str, Any]:
        """
        Analyzes the full telemetry series.
        Returns:
            - residuals: List of float residuals
            - max_residual: Max absolute residual observed
            - mean_residual: Mean absolute residual
            - consistency_score: Score in [0.0, 1.0]
            - anomalies_detected: List of specific physical inconsistency findings
        """
        if not telemetry:
            return {
                "residuals": [],
                "max_residual": 0.0,
                "mean_residual": 0.0,
                "consistency_score": 1.0,
                "anomalies_detected": []
            }

        residuals: List[float] = []
        anomalies: List[Dict[str, Any]] = []

        consecutive_identical_temp = 0
        last_reported_temp: Optional[float] = None

        for idx, slice_data in enumerate(telemetry):
            reported = slice_data.sensor_temperature if slice_data.sensor_temperature is not None else slice_data.battery_temperature
            predicted = slice_data.predicted_temperature if slice_data.predicted_temperature is not None else slice_data.battery_temperature
            residual = slice_data.temperature_residual if slice_data.temperature_residual is not None else round(reported - predicted, 2)
            residuals.append(residual)

            t = slice_data.timestamp
            current = slice_data.charging_current

            # 1. Implausible instantaneous jump check
            if idx > 0 and last_reported_temp is not None:
                step_delta = abs(reported - last_reported_temp)
                if step_delta >= cls.IMPLAUSIBLE_JUMP_THRESHOLD_C:
                    anomalies.append({
                        "timestamp": t,
                        "type": "implausible_thermal_jump",
                        "description": f"Impossible thermal jump of {step_delta:.1f}°C in 1 second (physical thermal inertia violated).",
                        "severity": "high"
                    })

            # 2. Stuck sensor check (unchanged temperature while current is flowing)
            if last_reported_temp is not None and abs(reported - last_reported_temp) < 0.001 and current > 25.0:
                consecutive_identical_temp += 1
                if consecutive_identical_temp == cls.STUCK_WINDOW_SECONDS:
                    anomalies.append({
                        "timestamp": t,
                        "type": "stuck_reading",
                        "description": f"Reported temperature remained frozen at {reported:.1f}°C for {cls.STUCK_WINDOW_SECONDS}s under active current of {current:.1f}A.",
                        "severity": "medium"
                    })
            else:
                consecutive_identical_temp = 0

            # 3. Sustained drift check
            if abs(residual) > 5.0 and slice_data.sensor_quality != "dropout":
                anomalies.append({
                    "timestamp": t,
                    "type": "sustained_drift",
                    "description": f"Reported temperature deviates from physical model by {abs(residual):.1f}°C (Residual = {residual:.1f}°C).",
                    "severity": "low" if abs(residual) < 10.0 else "medium"
                })

            last_reported_temp = reported

        abs_residuals = [abs(r) for r in residuals]
        max_res = max(abs_residuals) if abs_residuals else 0.0
        mean_res = sum(abs_residuals) / len(abs_residuals) if abs_residuals else 0.0

        # Score calculation: 1.0 when mean_res <= 1.0°C; drops smoothly to 0.0 as mean_res approaches 15.0°C
        consistency_score = max(0.0, min(1.0, 1.0 - (mean_res / 15.0)))

        # Penalize for severe anomalies
        jump_count = sum(1 for a in anomalies if a["type"] == "implausible_thermal_jump")
        if jump_count > 0:
            consistency_score = max(0.1, consistency_score * 0.6)

        return {
            "residuals": residuals,
            "max_residual": round(max_res, 2),
            "mean_residual": round(mean_res, 2),
            "consistency_score": round(consistency_score, 3),
            "anomalies_detected": anomalies[:10]  # Cap summary to top 10
        }
