"""
Scenario Builder Service (Feature F02).
Validates user-submitted scenario parameters, verifies safe whitelisted events,
constructs executable ScenarioSchema objects, and assigns safe unique IDs.
"""

import uuid
from typing import Dict, Any, List
from backend.app.schemas.scenario import ScenarioSchema, ScenarioCreateRequest
from backend.app.core.guard import SafeByDesignGuard


class ScenarioBuilder:

    @staticmethod
    def build_custom_scenario(req: ScenarioCreateRequest) -> ScenarioSchema:
        """
        Validates and instantiates a safe custom scenario.
        Generates a unique scenario ID prefix SCN-CUST-XXXX.
        """
        # Validate duration and seed
        SafeByDesignGuard.validate_simulation_parameters(req.default_seed, req.duration_seconds)

        # Validate events
        for ev in req.scheduled_events:
            SafeByDesignGuard.validate_event(ev.model_dump())
            if ev.timestamp > req.duration_seconds:
                raise ValueError(f"Event {ev.event_id} timestamp ({ev.timestamp}s) exceeds scenario duration ({req.duration_seconds}s).")

        scenario_id = f"SCN-CUST-{uuid.uuid4().hex[:6].upper()}"

        scenario = ScenarioSchema(
            scenario_id=scenario_id,
            name=req.name,
            family="Custom",
            description=req.description,
            duration_seconds=req.duration_seconds,
            default_seed=req.default_seed,
            components_involved=req.components_involved,
            scheduled_events=req.scheduled_events,
            expected_physical_effects=req.expected_physical_effects,
            ground_truth_links=[],
            expected_outcome="Custom user-defined execution outcome",
            safety_limitations=req.safety_limitations,
            sensor_noise_std=req.sensor_noise_std,
            cyber_timestamp_offset=req.cyber_timestamp_offset,
            telemetry_timestamp_offset=req.telemetry_timestamp_offset,
            defense_config=req.defense_config,
            is_custom=True,
            is_held_out=False
        )

        return scenario
