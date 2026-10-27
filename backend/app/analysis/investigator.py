"""
Investigator Guidance Service (Feature F41).
Generates an evidence-grounded, rule-based investigative checklist
with recommendations, reasons, target components, and evidence cross-references.
"""

from typing import List, Dict, Any, Optional
from backend.app.schemas.analysis import InvestigatorGuidance, InvestigatorItem, CorrelationLink
from backend.app.schemas.telemetry import TelemetryTimeSlice


class InvestigatorGuidanceEngine:

    @classmethod
    def generate_guidance(
        cls,
        run_id: str,
        correlation_links: List[CorrelationLink],
        telemetry: List[TelemetryTimeSlice],
        residual_stats: Dict[str, Any]
    ) -> InvestigatorGuidance:
        """
        Synthesizes observed evidence into a structured investigative checklist.
        """
        steps: List[InvestigatorItem] = []
        step_num = 1

        # Summary components
        peak_temp = max((s.battery_temperature for s in telemetry), default=25.0)
        peak_curr = max((s.charging_current for s in telemetry), default=0.0)
        tripped = any(s.charger_state == "FAULT" for s in telemetry)

        # 1. Inspect correlation links for cyber commands
        has_unauth_command = False
        has_can_spoof = False
        has_cooling_override = False

        for link in correlation_links:
            ev_type = link.event_type
            if "unauthorized" in link.explanation.lower() or "auth" in link.event_id.lower():
                has_unauth_command = True
                steps.append(InvestigatorItem(
                    step_number=step_num,
                    recommendation="Audit CSMS TLS session logs and inspect OCPP WebSocket token authentication.",
                    reason=f"Event {link.event_id} ({ev_type}) was executed without verified cryptographic authorization.",
                    supporting_evidence_id=link.link_id,
                    target_component="csms_backend",
                    status="pending"
                ))
                step_num += 1

            if "CAN_SPOOF" in ev_type:
                has_can_spoof = True
                steps.append(InvestigatorItem(
                    step_number=step_num,
                    recommendation="Isolate powertrain CAN bus segment and inspect gateway / telematics control unit (TCU) for rogue frames.",
                    reason=f"Event {link.event_id} injected synthetic frames bypassing standard vehicle authentication.",
                    supporting_evidence_id=link.link_id,
                    target_component="evse_controller",
                    status="pending"
                ))
                step_num += 1

            if ev_type == "DISABLE_COOLING":
                has_cooling_override = True
                steps.append(InvestigatorItem(
                    step_number=step_num,
                    recommendation="Inspect cooling system relay actuators and verify manual pump override interlocks.",
                    reason=f"Active charge session experienced deliberate cooling deactivation ({link.event_id}).",
                    supporting_evidence_id=link.link_id,
                    target_component="cooling_system",
                    status="pending"
                ))
                step_num += 1

        # 2. Inspect sensor residuals and faults
        anomalies = residual_stats.get("anomalies_detected", [])
        max_residual = residual_stats.get("max_residual", 0.0)

        if max_residual > 5.0 or anomalies:
            anomaly_types = ", ".join(set(a["type"] for a in anomalies)) or "deviating telemetry"
            steps.append(InvestigatorItem(
                step_number=step_num,
                recommendation="Perform analog probe sanity check, thermistor resistance testing, and ADC harness continuity validation.",
                reason=f"Physics consistency checker flagged {anomaly_types} with a maximum residual of {max_residual:.1f}°C against the Joule twin.",
                supporting_evidence_id="RESIDUAL-CHECK-01",
                target_component="battery_pack",
                status="pending"
            ))
            step_num += 1

        # 3. Hardware protection verification if tripped
        if tripped or peak_temp >= 70.0:
            steps.append(InvestigatorItem(
                step_number=step_num,
                recommendation="Inspect physical main contactors, pyrofuse status, and safety breaker tripping logs.",
                reason=f"Emergency protective shutdown was triggered (peak temperature: {peak_temp:.1f}°C). Verify contactor points did not weld.",
                supporting_evidence_id="TRIP-RECORD-01",
                target_component="hardware_safety_breaker",
                status="pending"
            ))
            step_num += 1

        # Default fallback step if nominal
        if not steps:
            steps.append(InvestigatorItem(
                step_number=1,
                recommendation="Review routine charger session logs and confirm steady-state thermal dissipation baseline.",
                reason="All physical telemetry and cyber message exchanges remained within expected nominal tolerances.",
                supporting_evidence_id="NOMINAL-01",
                target_component="evse_controller",
                status="verified"
            ))

        summary = (
            f"Run {run_id}: Peak current {peak_curr:.1f}A, peak temp {peak_temp:.1f}°C. "
            f"{'Protective trip observed. ' if tripped else ''}"
            f"Correlated {len(correlation_links)} cyber-physical links across {len(steps)} investigative priority items."
        )

        return InvestigatorGuidance(
            run_id=run_id,
            incident_summary=summary,
            suggested_steps=steps
        )
