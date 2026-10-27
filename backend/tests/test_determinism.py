"""
Tests for Seeded Determinism and Replay Consistency (Features F03, Acceptance Criteria 3 & 9).
"""

import pytest
from backend.app.scenarios.library import SCENARIOS_MAP
from backend.app.simulation.simulator import SimulationEngine
from backend.app.analysis.counterfactual import CounterfactualEngine


def test_identical_seed_produces_identical_results():
    """Criteria 3: The same seed and scenario produce identical results."""
    scenario = SCENARIOS_MAP["SCN-ATK-01"]
    seed = 4242

    run_1 = SimulationEngine.run(scenario, seed=seed)
    run_2 = SimulationEngine.run(scenario, seed=seed)

    # Validate high-level outputs
    assert run_1.peak_current == run_2.peak_current
    assert run_1.peak_temperature == run_2.peak_temperature
    assert run_1.final_soc == run_2.final_soc
    assert run_1.fault_triggered == run_2.fault_triggered
    assert len(run_1.telemetry) == len(run_2.telemetry)

    # Validate exact float values across every telemetry slice
    for p1, p2 in zip(run_1.telemetry, run_2.telemetry):
        assert p1.timestamp == p2.timestamp
        assert p1.battery_temperature == p2.battery_temperature
        assert p1.charging_current == p2.charging_current
        assert p1.battery_voltage == p2.battery_voltage
        assert p1.state_of_charge == p2.state_of_charge
        assert p1.cooling_power == p2.cooling_power


def test_counterfactual_replay_uses_identical_seed():
    """Criteria 9: Counterfactual replay uses identical initial conditions and seed."""
    scenario = SCENARIOS_MAP["SCN-ATK-01"]
    seed = 9999

    original_run = SimulationEngine.run(scenario, seed=seed)
    cf_res = CounterfactualEngine.run_replay(
        original_run=original_run,
        scenario=scenario,
        target_event_id="EVT-ATK-01-B"
    )

    assert cf_res.seed_used == seed
    assert cf_res.original_run_id == original_run.run_id
    assert len(cf_res.overlay_data) == len(original_run.telemetry)

    # Initial time steps (before event at t=15s) must be identical
    for pt in cf_res.overlay_data:
        if pt.timestamp < 15.0:
            assert pt.original_current == pt.replay_current
            assert pt.original_temperature == pt.replay_temperature
            assert pt.original_voltage == pt.replay_voltage
            assert pt.original_soc == pt.replay_soc
