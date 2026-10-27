"""
SQLAlchemy ORM models for CyberTrace AI persistent storage (Feature F51).
Stores scenarios, simulation runs, events, telemetry slices, correlation links, and counterfactual replays.
"""

from sqlalchemy import Column, String, Integer, Float, Boolean, Text, DateTime
from datetime import datetime, timezone
from backend.app.database.session import Base


class ScenarioModel(Base):
    __tablename__ = "scenarios"

    scenario_id = Column(String(64), primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    family = Column(String(64), nullable=False, index=True)
    description = Column(Text, nullable=False)
    duration_seconds = Column(Float, nullable=False, default=60.0)
    default_seed = Column(Integer, nullable=False, default=42)
    components_json = Column(Text, nullable=False)
    events_json = Column(Text, nullable=False)
    expected_physical_effects = Column(Text, nullable=False)
    ground_truth_links_json = Column(Text, nullable=False)
    expected_outcome = Column(Text, nullable=False)
    safety_limitations = Column(Text, nullable=False)
    is_custom = Column(Boolean, default=False)
    is_held_out = Column(Boolean, default=False)


class SimulationRunModel(Base):
    __tablename__ = "simulation_runs"

    run_id = Column(String(64), primary_key=True, index=True)
    scenario_id = Column(String(64), nullable=False, index=True)
    scenario_name = Column(String(255), nullable=False)
    scenario_family = Column(String(64), nullable=False)
    seed = Column(Integer, nullable=False)
    duration_seconds = Column(Float, nullable=False)
    is_counterfactual = Column(Boolean, default=False)
    omitted_event_id = Column(String(64), nullable=True)
    peak_current = Column(Float, nullable=False)
    peak_temperature = Column(Float, nullable=False)
    final_soc = Column(Float, nullable=False)
    fault_triggered = Column(Boolean, default=False)
    status = Column(String(32), default="COMPLETED")
    created_at = Column(String(64), default=lambda: datetime.now(timezone.utc).isoformat())

    # Full JSON payloads for exact replay and persistence
    events_json = Column(Text, nullable=False)
    telemetry_json = Column(Text, nullable=False)
    threshold_crossings_json = Column(Text, nullable=False, default="[]")


class CorrelationLinkModel(Base):
    __tablename__ = "correlation_links"

    link_id = Column(String(64), primary_key=True, index=True)
    run_id = Column(String(64), nullable=False, index=True)
    event_id = Column(String(64), nullable=False, index=True)
    event_type = Column(String(64), nullable=False)
    source = Column(String(64), nullable=False)
    target_signal = Column(String(64), nullable=False)
    target_component = Column(String(64), nullable=False)
    dependency_path_json = Column(Text, nullable=False)
    time_delay = Column(Float, nullable=False)
    observed_change = Column(Float, nullable=False)
    change_unit = Column(String(16), nullable=False)
    confidence_score = Column(Float, nullable=False)
    evidence_label = Column(String(32), nullable=False)  # Observed, Inferred, Uncertain
    rules_matched_json = Column(Text, nullable=False)
    explanation = Column(Text, nullable=False)
    uncertainty_notes = Column(Text, nullable=True)


class CounterfactualReplayModel(Base):
    __tablename__ = "counterfactual_replays"

    counterfactual_id = Column(String(64), primary_key=True, index=True)
    original_run_id = Column(String(64), nullable=False, index=True)
    counterfactual_run_id = Column(String(64), nullable=False, index=True)
    target_event_id = Column(String(64), nullable=False)
    seed_used = Column(Integer, nullable=False)
    peak_current_diff = Column(Float, nullable=False)
    peak_temp_diff = Column(Float, nullable=False)
    final_soc_diff = Column(Float, nullable=False)
    effect_attribution = Column(String(32), nullable=False)  # DISAPPEARED, DECREASED, UNCHANGED
    is_causally_proven = Column(Boolean, default=False)
    summary = Column(Text, nullable=False)
    limitations = Column(Text, nullable=False)
    overlay_json = Column(Text, nullable=False)
    created_at = Column(String(64), default=lambda: datetime.now(timezone.utc).isoformat())


class FleetRunModel(Base):
    __tablename__ = "fleet_runs"

    run_id = Column(String(64), primary_key=True, index=True)
    fleet_scenario_id = Column(String(64), nullable=False, index=True)
    charger_count = Column(Integer, nullable=False)
    feeder_capacity_kw = Column(Float, nullable=False)
    peak_fleet_power_kw = Column(Float, nullable=False)
    peak_feeder_loading_pct = Column(Float, nullable=False)
    min_feeder_voltage_v = Column(Float, nullable=False)
    overload_duration_seconds = Column(Float, nullable=False)
    affected_chargers_json = Column(Text, nullable=False, default="[]")
    summary_json = Column(Text, nullable=False, default="{}")
    created_at = Column(String(64), default=lambda: datetime.now(timezone.utc).isoformat())
