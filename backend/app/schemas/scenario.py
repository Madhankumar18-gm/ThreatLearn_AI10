"""
Scenario schema definitions (Features F01, F02, F04, F05).
Covers the 8 primary scenario families, ground-truth benchmark links,
custom scenario creation, noise and clock skew parameters, and import/export.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from backend.app.schemas.events import SimulatedEventSchema
from backend.app.schemas.defense import DefenseConfiguration


class GroundTruthLinkSchema(BaseModel):
    event_id: str = Field(..., description="Source event ID")
    target_signal: str = Field(..., description="Target physical signal affected")
    is_causal: bool = Field(..., description="True if the event genuinely causes the physical change")
    expected_delay_min: float = Field(0.0, description="Minimum expected physical response time (s)")
    expected_delay_max: float = Field(60.0, description="Maximum expected physical response time (s)")
    rationale: str = Field(..., description="Physics explanation of the ground-truth relationship")


class ScenarioSchema(BaseModel):
    scenario_id: str = Field(..., description="Unique scenario ID (e.g. SCN-NORM-01)")
    name: str = Field(..., description="Human-readable scenario title")
    family: str = Field(
        ...,
        description="Scenario family: Normal operation, Attack, Sensor fault, Benign high-power event, Delayed attack, Masked attack, Fleet attack, Defended attack"
    )
    description: str = Field(..., description="Detailed description of the scenario narrative")
    duration_seconds: float = Field(default=60.0, description="Total simulation length in seconds")
    default_seed: int = Field(default=42, description="Default deterministic random seed")
    components_involved: List[str] = Field(default_factory=list, description="List of architecture components involved")
    scheduled_events: List[SimulatedEventSchema] = Field(default_factory=list, description="List of time-scheduled simulated events")
    expected_physical_effects: str = Field(..., description="Summary of expected physical reactions")
    ground_truth_links: List[GroundTruthLinkSchema] = Field(default_factory=list, description="Ground truth causal links for benchmarking")
    expected_outcome: str = Field(..., description="Expected diagnostic outcome")
    safety_limitations: str = Field(..., description="Model limitations and real-world safety disclaimer")

    # Tier 2 Advanced Simulation Controls (Feature F04)
    sensor_noise_std: float = Field(default=0.05, description="Telemetry measurement noise std dev (°C or A)")
    cyber_timestamp_offset: float = Field(default=0.0, description="Clock skew offset for cyber events (seconds)")
    telemetry_timestamp_offset: float = Field(default=0.0, description="Clock skew offset for telemetry measurements (seconds)")
    measurement_jitter_std: float = Field(default=0.0, description="Optional measurement timing jitter std dev (seconds)")
    
    # Tier 2 Defenses & Metadata
    defense_config: Optional[DefenseConfiguration] = Field(default=None, description="Predefined or configured defenses")
    is_custom: bool = Field(default=False, description="True if authored via Scenario Builder")
    is_held_out: bool = Field(default=False, description="True if designated for held-out evaluation benchmarking")


class ScenarioCreateRequest(BaseModel):
    name: str = Field(..., min_length=3, max_length=120)
    family: str = Field(default="Custom")
    description: str = Field(..., min_length=5, max_length=1000)
    duration_seconds: float = Field(default=60.0, ge=10.0, le=300.0)
    default_seed: int = Field(default=42, ge=0)
    components_involved: List[str] = Field(default_factory=lambda: ["csms_backend", "evse_controller", "power_converter", "battery_pack", "cooling_system"])
    scheduled_events: List[SimulatedEventSchema] = Field(..., min_length=1)
    expected_physical_effects: str = Field(default="Custom user-defined scenario effects")
    safety_limitations: str = Field(default="Simulation model results only; illustrative defensive research testbed.")
    sensor_noise_std: float = Field(default=0.05, ge=0.0, le=5.0)
    cyber_timestamp_offset: float = Field(default=0.0, ge=-30.0, le=30.0)
    telemetry_timestamp_offset: float = Field(default=0.0, ge=-30.0, le=30.0)
    defense_config: Optional[DefenseConfiguration] = None


class ScenarioExportSchema(BaseModel):
    schema_version: str = Field(default="2.0.0", description="ThreatLens scenario schema version")
    exported_at: str
    scenario: ScenarioSchema
