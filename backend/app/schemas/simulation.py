"""
Simulation API request and response schemas (Features F03, F04, F06-F16, F39).
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from backend.app.schemas.events import SimulatedEventSchema
from backend.app.schemas.telemetry import TelemetryTimeSlice
from backend.app.schemas.defense import DefenseConfiguration, DefenseIntervention


class SimulationRunRequest(BaseModel):
    scenario_id: str = Field(..., description="ID of scenario to simulate")
    seed: Optional[int] = Field(None, description="Optional custom deterministic random seed")
    omitted_event_id: Optional[str] = Field(None, description="Event ID to omit for counterfactual replay")
    
    # Tier 2 Advanced Simulation Overrides
    custom_defenses: Optional[DefenseConfiguration] = Field(None, description="Optional overrides for defense toggles")
    cyber_timestamp_offset: Optional[float] = Field(None, description="Optional override for cyber event clock offset (s)")
    telemetry_timestamp_offset: Optional[float] = Field(None, description="Optional override for telemetry clock offset (s)")
    sensor_noise_std: Optional[float] = Field(None, description="Optional override for sensor measurement noise std dev")


class ThresholdCrossing(BaseModel):
    timestamp: float
    signal: str
    threshold_type: str  # "warning" or "critical"
    threshold_value: float
    observed_value: float
    unit: str
    description: str


class SimulationRunResponse(BaseModel):
    run_id: str
    scenario_id: str
    scenario_name: str
    scenario_family: str
    seed: int
    duration_seconds: float
    created_at: str
    status: str
    is_counterfactual: bool
    omitted_event_id: Optional[str] = None
    events: List[SimulatedEventSchema] = Field(default_factory=list)
    telemetry: List[TelemetryTimeSlice] = Field(default_factory=list)
    peak_current: float
    peak_temperature: float
    final_soc: float
    fault_triggered: bool
    threshold_crossings: List[ThresholdCrossing] = Field(default_factory=list)

    # Tier 2 Advanced Additions
    defense_interventions: List[DefenseIntervention] = Field(default_factory=list)
    cyber_timestamp_offset: float = 0.0
    telemetry_timestamp_offset: float = 0.0
    sensor_noise_std: float = 0.05


class RunSummary(BaseModel):
    run_id: str
    scenario_id: str
    scenario_name: str
    scenario_family: str
    seed: int
    duration_seconds: float
    created_at: str
    status: str
    is_counterfactual: bool
    omitted_event_id: Optional[str] = None
    peak_current: float
    peak_temperature: float
    fault_triggered: bool
