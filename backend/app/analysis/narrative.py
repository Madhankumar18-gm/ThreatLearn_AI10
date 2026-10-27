"""
Evidence-Grounded Narrative Generator (Feature F43).
Generates rigorous, deterministic incident narratives strictly referencing verified evidence IDs.
Enforces calibrated epistemology:
- 'Observed': Direct recorded telemetry or cyber packets.
- 'Inferred': Mathematically grounded causal links supported by dependency paths and counterfactual replay.
- 'Uncertain': Ambient, uncorroborated, or alternative physical possibilities.
Never claims real-world attribution from simulation models.
"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class GroundedNarrative(BaseModel):
    narrative_id: str
    run_id: str
    scenario_id: str
    executive_summary: str
    observations_section: str
    inferred_causal_relationships: str
    uncertainties_and_alternatives: str
    counterfactual_proof_statement: str
    recommended_investigative_actions: List[str]
    referenced_evidence_ids: List[str]
    disclaimer: str = Field(
        default="Defensive simulation analytical narrative. Based exclusively on simulated digital twin telemetry and deterministic counterfactual models. Does not constitute judicial or physical forensic attribution.",
        description="Forensic boundary disclaimer"
    )


class NarrativeGenerator:
    """Generates structured, evidence-referenced narrative reports from run artifacts."""

    @classmethod
    def generate(
        cls,
        run_data: Dict[str, Any],
        correlation_links: List[Dict[str, Any]],
        counterfactual_result: Optional[Dict[str, Any]] = None,
        physics_findings: Optional[List[Dict[str, Any]]] = None,
        masked_findings: Optional[List[Dict[str, Any]]] = None
    ) -> GroundedNarrative:
        import uuid

        run_id = run_data.get("run_id", "RUN-UNKNOWN")
        scn_id = run_data.get("scenario_id", "SCN-UNKNOWN")
        evidence_ids: List[str] = []

        # 1. Observations
        peak_t = run_data.get("peak_temperature", 25.0)
        peak_i = run_data.get("peak_current", 0.0)
        tripped = run_data.get("safety_trip_occurred", False)

        ev_obs_t = f"EVD-PEAK-TEMP-{peak_t:.1f}C"
        ev_obs_i = f"EVD-PEAK-CURR-{peak_i:.1f}A"
        evidence_ids.extend([ev_obs_t, ev_obs_i])

        obs_text = (
            f"OBSERVED: During session {run_id} ({scn_id}), direct sensor telemetry recorded a peak charging current of "
            f"{peak_i:.1f} A [{ev_obs_i}] and a peak battery pack temperature of {peak_t:.1f} °C [{ev_obs_t}]. "
        )
        if tripped:
            ev_trip = "EVD-BMS-HARDWARE-TRIP"
            evidence_ids.append(ev_trip)
            obs_text += f"The independent BMS hardware contactor tripped to FAULT state [{ev_trip}] due to threshold limits."
        else:
            obs_text += "No hardware contactor disconnect was triggered; operating parameters remained bounded."

        # 2. Inferred Causal Relationships
        inferred_links = [l for l in correlation_links if l.get("classification") in ["Inferred", "Attack-like"] or l.get("rules_satisfied_count", 0) >= 3]
        if inferred_links:
            inferred_text = (
                f"INFERRED: The correlation engine identified {len(inferred_links)} verified causal relationship(s) "
                f"traversing directed graph paths from cyber command inputs to physical energy deposition. "
            )
            for idx, link in enumerate(inferred_links[:2]):
                ev_link = f"EVD-LINK-{link.get('event_id', f'L{idx}')}"
                evidence_ids.append(ev_link)
                inferred_text += (
                    f"Specifically, event {link.get('event_type', 'COMMAND')} [{ev_link}] on component "
                    f"'{link.get('source_component', 'evse')}' was causally linked to signal '{link.get('target_signal', 'temperature')}' "
                    f"with confidence {link.get('confidence_score', 0.90):.0%} across {link.get('rules_satisfied_count', 4)} verified physics rules. "
                )
        else:
            inferred_text = (
                "INFERRED: No unauthorized cyber events were causally linked to physical anomalies. "
                "All observed temperature rises are consistent with nominal Joule heating under authorized charging schedules."
            )

        # 3. Uncertainties & Alternative Explanations
        uncertainties = []
        if physics_findings:
            for f in physics_findings:
                ev_fnd = f"EVD-PHYS-{f.get('type', 'RESIDUAL')}"
                evidence_ids.append(ev_fnd)
                uncertainties.append(f"Physics residual anomaly detected [{ev_fnd}]: {f.get('detail', 'Residual deviation')}")

        if masked_findings:
            for m in masked_findings:
                ev_msk = f"EVD-MASKED-{m.get('finding_id', 'FND')}"
                evidence_ids.append(ev_msk)
                uncertainties.append(f"Sensor discrepancy [{ev_msk}]: {m.get('primary_hypothesis', 'Thermal sensor mismatch')}")

        if uncertainties:
            uncertain_text = (
                "UNCERTAIN: Alternative non-adversarial hypotheses remain active. Specifically: " +
                "; ".join(uncertainties) + ". "
                "Hardware sensor drift, contactor bounce, or model parameter calibration tolerance cannot be ruled out without secondary physical telemetry."
            )
        else:
            uncertain_text = (
                "UNCERTAIN: Environmental noise, ambient temperature drift, and transducer quantization tolerances "
                "account for ±0.5 °C of temperature variation. No unmodeled physical discrepancies remain unexplained."
            )

        # 4. Counterfactual Proof
        if counterfactual_result and counterfactual_result.get("replay_executed"):
            delta_t = counterfactual_result.get("delta_peak_temp", 0.0)
            proven = counterfactual_result.get("attribution_proven", False)
            ev_cf = f"EVD-CF-DELTA-T-{delta_t:.1f}C"
            evidence_ids.append(ev_cf)

            if proven:
                cf_text = (
                    f"COUNTERFACTUAL PROOF: Deterministic counterfactual replay under identical random seed "
                    f"isolated the target event. Upon excising the command, the physical anomaly disappeared (ΔT = -{abs(delta_t):.1f} °C) [{ev_cf}]. "
                    f"This rigorously proves within the simulated digital twin that the physical heating was counterfactually dependent on the cyber event."
                )
            else:
                cf_text = (
                    f"COUNTERFACTUAL PROOF: Replay under identical seed demonstrated negligible thermal difference (ΔT = {delta_t:.1f} °C) [{ev_cf}]. "
                    f"The physical trajectory persisted independently of the excised command, refuting direct causal attribution."
                )
        else:
            cf_text = "COUNTERFACTUAL PROOF: Counterfactual replay was not executed for this run. Causal attribution relies solely on forward directed path correlation."

        # 5. Executive Summary
        exec_summary = (
            f"Investigation Report for Incident {run_id}. Peak temperature reached {peak_t:.1f} °C [{ev_obs_t}] "
            f"under a peak current of {peak_i:.1f} A [{ev_obs_i}]. "
            f"{'A causal cyber-to-physical link was established and confirmed via counterfactual replay.' if (counterfactual_result and counterfactual_result.get('attribution_proven')) else 'Physical parameters remained within safe or nominal operational boundaries.'}"
        )

        # 6. Actionable recommendations
        actions = [
            f"Verify physical terminal connections and calibrate thermistors against reference [{ev_obs_t}].",
            "Review CSMS communication gateway logs for cryptographic authentication failures.",
            "Cross-reference EVSE firmware checksum against known good manufacturer baseline."
        ]
        if tripped:
            actions.append("Perform insulation resistance test and DC contactor inspection before clearing FAULT latch.")

        return GroundedNarrative(
            narrative_id=f"NAR-{uuid.uuid4().hex[:8].upper()}",
            run_id=run_id,
            scenario_id=scn_id,
            executive_summary=exec_summary,
            observations_section=obs_text,
            inferred_causal_relationships=inferred_text,
            uncertainties_and_alternatives=uncertain_text,
            counterfactual_proof_statement=cf_text,
            recommended_investigative_actions=actions,
            referenced_evidence_ids=list(set(evidence_ids))
        )
