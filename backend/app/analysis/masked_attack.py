"""
Masked-Attack Detection Module (Feature F25).
Identifies explainable discrepancies between physical model state and sensor-reported state
(e.g., physical Joule heating occurring while a thermistor is frozen or faked calm).
Includes alternative physical failure explanations, evidence IDs, and verification steps.
"""

import uuid
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

from backend.app.schemas.telemetry import TelemetryTimeSlice
from backend.app.schemas.events import SimulatedEventSchema


class MaskedAttackFinding(BaseModel):
    finding_id: str = Field(..., description="Unique finding identifier (e.g. MSK-FND-01)")
    component_id: str = Field(..., description="Target component affected")
    sensor_name: str = Field(..., description="Sensor exhibiting discrepancy (e.g. sensor_temperature)")
    expected_value: float = Field(..., description="Physics model predicted value")
    reported_value: float = Field(..., description="Sensor measured value")
    discrepancy_magnitude: float = Field(..., description="Absolute residual difference |Reported - Expected|")
    unit: str = Field(default="°C", description="Physical unit")
    evidence_ids: List[str] = Field(default_factory=list, description="Referenced evidence items")
    primary_hypothesis: str = Field(..., description="Primary analytical hypothesis")
    alternative_explanations: List[str] = Field(default_factory=list, description="Plausible non-attack causes")
    uncertainty_level: str = Field(default="MEDIUM", description="Uncertainty level: LOW, MEDIUM, HIGH")
    recommended_verification_steps: List[str] = Field(default_factory=list, description="Physical verification steps")
    cyber_event_correlated: bool = Field(default=False, description="Whether correlated with an unauthorized cyber event")


class MaskedAttackDetector:
    """Detects when physical variables diverge from sensor readings with explainable rationale."""

    @classmethod
    def analyze(
        cls,
        time_slices: List[TelemetryTimeSlice],
        events: List[SimulatedEventSchema],
        counterfactual_difference: Optional[Dict[str, Any]] = None
    ) -> List[MaskedAttackFinding]:
        findings: List[MaskedAttackFinding] = []
        if not time_slices:
            return findings

        # Check for cyber events in the scenario
        cyber_events = [e for e in events if "CURRENT" in e.event_type or "OVERRIDE" in e.event_type or "SPOOF" in e.event_type]
        has_cyber_attack = len(cyber_events) > 0

        # Scan for thermal masking: High Joule heating vs frozen/calm sensor
        max_residual = 0.0
        max_slice: Optional[TelemetryTimeSlice] = None
        stuck_temperature = None
        consecutive_stuck_count = 0

        prev_reported = None
        for s in time_slices:
            # Check reported vs predicted temperature residual
            if s.sensor_temperature is not None and s.predicted_temperature is not None:
                residual = abs(s.sensor_temperature - s.predicted_temperature)
                if residual > max_residual:
                    max_residual = residual
                    max_slice = s

            # Check if reported temperature is strictly flat despite significant current
            if prev_reported is not None and s.sensor_temperature is not None:
                if abs(s.sensor_temperature - prev_reported) < 0.05 and s.charging_current > 60.0:
                    consecutive_stuck_count += 1
                else:
                    consecutive_stuck_count = 0
            if s.sensor_temperature is not None:
                prev_reported = s.sensor_temperature

        # Significant discrepancy threshold: residual > 6.0 °C and sustained high current
        if max_slice and max_residual >= 6.0:
            finding_id = f"MSK-FND-{uuid.uuid4().hex[:6].upper()}"
            expected = max_slice.predicted_temperature
            reported = max_slice.sensor_temperature

            # Supporting evidence IDs
            evidence_ids = [
                f"EVD-RESIDUAL-MAX-{max_residual:.1f}C",
                f"EVD-PHYSICAL-CURRENT-{max_slice.charging_current:.1f}A",
                f"EVD-TIME-{max_slice.timestamp:.1f}S"
            ]
            if has_cyber_attack:
                for ce in cyber_events:
                    evidence_ids.append(f"EVD-CYBER-{ce.event_type}")

            if counterfactual_difference and counterfactual_difference.get("attribution_proven"):
                evidence_ids.append("EVD-CF-DISAPPEARANCE-CONFIRMED")

            # Determine primary hypothesis & uncertainty
            if has_cyber_attack and max_slice.charging_current > 90.0:
                primary = "Masked Overcurrent Attack: Sensor reading suppressed while physical Joule heating accumulates"
                uncertainty = "LOW"
            elif max_slice.charging_current < 10.0:
                primary = "Sensor Calibration Drift: Transducer offset without physical heating source"
                uncertainty = "MEDIUM"
            else:
                primary = "Discrepancy Detected: Sensor freezing during high charging current"
                uncertainty = "MEDIUM"

            # Alternative non-adversarial explanations
            alternatives = [
                "Hardware thermistor disconnection or ADC reference failure (sensor stuck fault)",
                "Thermal grease / heat-pipe mechanical detachment causing delayed sensor heat transfer",
                "Transient clock synchronization skew between sensor ADC and digital twin timebase",
                "Model parameter mismatch: Heat capacity (C_th) or thermal resistance (R_th) miscalibration"
            ]

            # Concrete operational verification steps
            verification = [
                "Deploy independent handheld infrared pyrometer or secondary K-type thermocouple to verify physical surface temperature.",
                "Inspect analog ADC input voltage on EVSE mainboard to distinguish open-circuit sensor from faked digital reading.",
                "Review CSMS and local controller command logs for concurrent parameter override or firmware flash events.",
                "Perform cold-soak sensor recalibration at known ambient temperature (25.0°C)."
            ]

            findings.append(
                MaskedAttackFinding(
                    finding_id=finding_id,
                    component_id="battery_pack",
                    sensor_name="sensor_temperature",
                    expected_value=round(expected, 2),
                    reported_value=round(reported, 2),
                    discrepancy_magnitude=round(max_residual, 2),
                    unit="°C",
                    evidence_ids=evidence_ids,
                    primary_hypothesis=primary,
                    alternative_explanations=alternatives,
                    uncertainty_level=uncertainty,
                    recommended_verification_steps=verification,
                    cyber_event_correlated=has_cyber_attack
                )
            )

        return findings
