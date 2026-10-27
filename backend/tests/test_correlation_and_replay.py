"""
Tests for Correlation Engine, Dependency Validation, and Counterfactual Replay
(Features F20, F21, F22, Acceptance Criteria 7, 8, 10, 11, 12).
"""

import pytest
from backend.app.scenarios.library import SCENARIOS_MAP
from backend.app.simulation.simulator import SimulationEngine
from backend.app.analysis.correlation_engine import CorrelationEngine
from backend.app.analysis.counterfactual import CounterfactualEngine
from backend.app.analysis.dependency_graph import dependency_graph
from backend.app.schemas.analysis import EvidenceLabel


def test_correlation_engine_rejects_links_without_valid_dependency_paths():
    """Criteria 7: The correlation engine rejects links without valid dependency paths."""
    # Verify graph path truth:
    # There is NO path from temperature_sensor to grid_load
    assert not dependency_graph.has_dependency_path("temperature_sensor", "grid_load")
    # There is NO path from cooling_system to charging_current
    assert not dependency_graph.has_dependency_path("cooling_system", "charging_current")

    # Run attack scenario and inspect all generated links
    run = SimulationEngine.run(SCENARIOS_MAP["SCN-ATK-01"])
    links = CorrelationEngine.analyze_run(run)

    for link in links:
        # Every accepted link MUST have a valid path in the graph
        assert dependency_graph.has_dependency_path(link.dependency_path[0], link.target_signal)


def test_incompatible_event_and_signal_types_do_not_create_links():
    """Criteria 8: Incompatible event and signal types do not create links."""
    run = SimulationEngine.run(SCENARIOS_MAP["SCN-FLT-01"])  # Sensor fault scenario
    links = CorrelationEngine.analyze_run(run)

    for link in links:
        if link.event_type == "SENSOR_INJECT_FAULT":
            # Sensor fault cannot link to charging current or grid load
            assert link.target_signal != "charging_current"
            assert link.target_signal != "grid_load"


def test_counterfactual_produces_measurable_difference_for_attack():
    """Criteria 10: Removing an event produces a measurable difference when designed to affect the simulated outcome."""
    scenario = SCENARIOS_MAP["SCN-ATK-01"]  # 150A overcurrent attack
    run = SimulationEngine.run(scenario, seed=123)

    cf_res = CounterfactualEngine.run_replay(
        original_run=run,
        scenario=scenario,
        target_event_id="EVT-ATK-01-B"  # The unauthorized 150A current override
    )

    assert cf_res.is_causally_proven is True
    assert cf_res.effect_attribution in ("DISAPPEARED", "DECREASED")
    assert cf_res.peak_current_diff > 50.0  # Significant current reduction
    assert cf_res.peak_temp_diff > 2.0      # Measurable temperature reduction


def test_normal_scenarios_do_not_produce_fabricated_attack_impacts():
    """Criteria 11: Normal scenarios do not produce fabricated attack impacts."""
    scenario = SCENARIOS_MAP["SCN-NORM-01"]
    run = SimulationEngine.run(scenario)
    assert run.fault_triggered is False

    links = CorrelationEngine.analyze_run(run)
    for link in links:
        # Normal scenarios must not be labeled as Inferred malicious attacks
        assert link.evidence_label != EvidenceLabel.INFERRED, (
            f"Normal event {link.event_id} improperly labeled as INFERRED attack link!"
        )


def test_sensor_fault_and_benign_scenarios_do_not_become_attack_links():
    """Criteria 12: Sensor-fault and benign scenarios do not automatically become attack links."""
    # Test Sensor Fault scenario
    flt_run = SimulationEngine.run(SCENARIOS_MAP["SCN-FLT-01"])
    flt_links = CorrelationEngine.analyze_run(flt_run)
    for l in flt_links:
        if l.event_type == "SENSOR_INJECT_FAULT":
            assert l.evidence_label == EvidenceLabel.OBSERVED
            assert "malfunction" in l.explanation.lower() or "sensor" in l.explanation.lower()

    # Test Benign High-Power scenario
    bng_run = SimulationEngine.run(SCENARIOS_MAP["SCN-BNG-01"])
    bng_links = CorrelationEngine.analyze_run(bng_run)
    for l in bng_links:
        assert l.evidence_label != EvidenceLabel.INFERRED
        assert "authorized" in l.explanation.lower() or "normal" in l.explanation.lower()
