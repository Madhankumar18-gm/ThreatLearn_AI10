"""
Tests for Scenario Library (Features F01, Acceptance Criteria 1 & 2).
Verifies that at least 25 scenarios exist across 8 families, with unique IDs and valid schemas.
"""

import pytest
from backend.app.scenarios.library import build_scenario_library, SCENARIOS_MAP
from backend.app.schemas.scenario import ScenarioSchema


EXPECTED_FAMILIES = {
    "Normal operation",
    "Attack",
    "Sensor fault",
    "Benign high-power event",
    "Delayed attack",
    "Masked attack",
    "Fleet attack",
    "Defended attack"
}


def test_at_least_25_scenarios_available():
    """Criteria 1: At least 25 labelled scenarios are available."""
    scenarios = build_scenario_library()
    assert len(scenarios) >= 25, f"Expected >= 25 scenarios, found {len(scenarios)}"


def test_all_eight_families_represented():
    """Criteria 1: Scenarios span all eight primary families."""
    scenarios = build_scenario_library()
    present_families = {s.family for s in scenarios}
    for fam in EXPECTED_FAMILIES:
        assert fam in present_families, f"Missing required scenario family: {fam}"


def test_every_scenario_has_unique_id_and_valid_schema():
    """Criteria 2: Every scenario has a unique ID and valid schema."""
    scenarios = build_scenario_library()
    seen_ids = set()
    for s in scenarios:
        assert isinstance(s, ScenarioSchema)
        assert s.scenario_id not in seen_ids, f"Duplicate scenario ID found: {s.scenario_id}"
        seen_ids.add(s.scenario_id)

        assert len(s.name) > 3, "Scenario name too short"
        assert len(s.description) > 10, "Scenario description too short"
        assert s.duration_seconds > 0, "Scenario duration must be positive"
        assert s.default_seed >= 0, "Scenario seed must be non-negative"
        assert len(s.components_involved) > 0, "Scenario must specify components involved"
        assert len(s.expected_physical_effects) > 5, "Expected physical effects must be documented"
        assert len(s.expected_outcome) > 5, "Expected outcome must be documented"
        assert len(s.safety_limitations) > 5, "Safety limitations must be documented"


def test_scenario_scheduled_events_valid():
    """Verifies that all scheduled events have valid timestamps within scenario duration."""
    scenarios = build_scenario_library()
    for s in scenarios:
        for ev in s.scheduled_events:
            assert 0 <= ev.timestamp <= s.duration_seconds, (
                f"Event {ev.event_id} in {s.scenario_id} has invalid timestamp {ev.timestamp} "
                f"outside duration {s.duration_seconds}"
            )
            from backend.app.core.guard import SafeByDesignGuard
            assert ev.event_type in SafeByDesignGuard.ALLOWED_EVENT_TYPES
