"""
Counterfactual Replay Engine (Features F22, F32).
Proves simulated cyberattack impact through deterministic counterfactual replay:
Reruns the scenario under identical initial conditions and seed, omitting only the target event.
Quantifies delta metrics, provides trace overlay data, and labels effect attribution honestly.
"""

from typing import Optional, List, Dict, Any
from backend.app.schemas.scenario import ScenarioSchema
from backend.app.schemas.simulation import SimulationRunResponse
from backend.app.schemas.analysis import CounterfactualResponse, CounterfactualOverlayPoint
from backend.app.simulation.simulator import SimulationEngine


class CounterfactualEngine:

    @staticmethod
    def run_replay(
        original_run: SimulationRunResponse,
        scenario: ScenarioSchema,
        target_event_id: str
    ) -> CounterfactualResponse:
        """
        Executes counterfactual replay by re-running the scenario with identical seed
        and initial state, omitting only the selected target_event_id.
        """
        # Execute counterfactual run with exact same seed
        replay_run: SimulationRunResponse = SimulationEngine.run(
            scenario=scenario,
            seed=original_run.seed,
            omitted_event_id=target_event_id
        )

        # Delta metrics: Original minus Replay
        peak_current_diff = round(original_run.peak_current - replay_run.peak_current, 2)
        peak_temp_diff = round(original_run.peak_temperature - replay_run.peak_temperature, 2)
        final_soc_diff = round(original_run.final_soc - replay_run.final_soc, 2)

        # Build synchronous overlay points for frontend charts
        orig_map = {slice_point.timestamp: slice_point for slice_point in original_run.telemetry}
        replay_map = {slice_point.timestamp: slice_point for slice_point in replay_run.telemetry}

        overlay_data: List[CounterfactualOverlayPoint] = []
        all_timestamps = sorted(set(orig_map.keys()) | set(replay_map.keys()))

        for t in all_timestamps:
            orig = orig_map.get(t)
            rep = replay_map.get(t)
            if orig and rep:
                overlay_data.append(CounterfactualOverlayPoint(
                    timestamp=t,
                    original_temperature=orig.battery_temperature,
                    replay_temperature=rep.battery_temperature,
                    original_current=orig.charging_current,
                    replay_current=rep.charging_current,
                    original_voltage=orig.battery_voltage,
                    replay_voltage=rep.battery_voltage,
                    original_soc=orig.state_of_charge,
                    replay_soc=rep.state_of_charge
                ))

        # Check if warning/critical thresholds were avoided in counterfactual
        orig_had_fault = original_run.fault_triggered
        replay_had_fault = replay_run.fault_triggered

        # Effect attribution classification: DISAPPEARED, DECREASED, UNCHANGED
        if (peak_temp_diff >= 3.0 or peak_current_diff >= 15.0 or (orig_had_fault and not replay_had_fault)):
            effect_attribution = "DISAPPEARED"
            is_causally_proven = True
            summary = (
                f"Counterfactual replay PROVES causal attribution: When event '{target_event_id}' was omitted, "
                f"peak battery temperature dropped by {peak_temp_diff:.1f}°C (from {original_run.peak_temperature}°C to {replay_run.peak_temperature}°C), "
                f"and peak current dropped by {peak_current_diff:.1f}A."
            )
            if orig_had_fault and not replay_had_fault:
                summary += " Hardware fault trip was completely avoided in the replay."
        elif (peak_temp_diff >= 0.8 or peak_current_diff >= 5.0):
            effect_attribution = "DECREASED"
            is_causally_proven = True
            summary = (
                f"Counterfactual replay shows PARTIAL effect reduction: Removing event '{target_event_id}' reduced "
                f"peak temperature by {peak_temp_diff:.1f}°C and current by {peak_current_diff:.1f}A, indicating partial causal contribution."
            )
        else:
            effect_attribution = "UNCHANGED"
            is_causally_proven = False
            summary = (
                f"Counterfactual replay shows NO measurable physical difference (peak temp delta: {peak_temp_diff:+.1f}°C, "
                f"current delta: {peak_current_diff:+.1f}A). Event '{target_event_id}' had no causal impact on the physical outcome."
            )

        limitations = (
            "Model Scope Limitation: Counterfactual proof is established within the mathematical constraints "
            "of this simulation model and initial conditions. It does not constitute certified proof of physical hardware immunity. "
            "Real-world validation requires calibrated bench telemetry, environmental testing, and hardware-in-the-loop (HIL) verification."
        )

        return CounterfactualResponse(
            original_run_id=original_run.run_id,
            counterfactual_run_id=replay_run.run_id,
            target_event_id=target_event_id,
            seed_used=original_run.seed,
            peak_current_diff=peak_current_diff,
            peak_temp_diff=peak_temp_diff,
            final_soc_diff=final_soc_diff,
            effect_attribution=effect_attribution,
            is_causally_proven=is_causally_proven,
            summary=summary,
            limitations=limitations,
            overlay_data=overlay_data
        )
