"""
Fleet and Grid Feeder Schemas (Features F09, F10, F37).
Provides structured definitions for multi-charger fleet digital twin (10-50 chargers)
and shared grid feeder power/voltage loading dynamics.
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional


class FeederConfig(BaseModel):
    feeder_id: str = Field(default="FEEDER-MAIN-01", description="Unique identifier for substation distribution feeder")
    feeder_name: str = Field(default="Substation Feeder 4A (400V Distribution)", description="Descriptive feeder label")
    capacity_kw: float = Field(default=800.0, ge=100.0, le=5000.0, description="Rated feeder active power capacity in kW")
    nominal_voltage_v: float = Field(default=400.0, ge=200.0, le=1000.0, description="Nominal phase-to-phase AC distribution voltage")
    voltage_sag_alpha: float = Field(default=0.06, ge=0.01, le=0.20, description="Linear voltage drop coefficient per unit load")
    voltage_sag_beta: float = Field(default=0.02, ge=0.0, le=0.10, description="Quadratic non-linear voltage drop coefficient")
    warning_threshold_pct: float = Field(default=80.0, ge=50.0, le=95.0, description="Warning load threshold percentage")
    critical_threshold_pct: float = Field(default=95.0, ge=80.0, le=120.0, description="Critical overload threshold percentage")


class ChargerFleetSummary(BaseModel):
    charger_id: str = Field(..., description="Unique EVSE charger ID (e.g. CHG-01)")
    component_id: str = Field(..., description="Internal component reference")
    state: str = Field(default="CHARGING", description="Charger operating state: IDLE, CHARGING, FAULT")
    current_a: float = Field(..., description="Actual output current in Amperes")
    voltage_v: float = Field(..., description="DC charging bus voltage in Volts")
    power_kw: float = Field(..., description="Individual charger electrical demand in kW")
    battery_soc: float = Field(..., description="Vehicle battery state of charge (0-100%)")
    battery_temp_c: float = Field(..., description="Lumped battery pack temperature in °C")
    cooling_state: str = Field(default="NORMAL", description="Cooling subsystem status: NORMAL, OFF, OVERRIDDEN")
    is_affected: bool = Field(default=False, description="Flag indicating if charger is targeted by a cyber event or fault")
    active_event: Optional[str] = Field(default=None, description="Label of any active simulated event affecting this charger")


class FleetTimeSlice(BaseModel):
    timestamp: float = Field(..., description="Simulation time in seconds from start")
    total_fleet_power_kw: float = Field(..., description="Sum of active power drawn by all chargers in kW")
    total_fleet_current_a: float = Field(..., description="Sum of charging currents in Amperes")
    feeder_loading_pct: float = Field(..., description="Feeder loading percentage (total_power / capacity_kw * 100)")
    feeder_voltage_v: float = Field(..., description="Estimated feeder voltage under current load")
    feeder_status: str = Field(..., description="Feeder state: NORMAL, WARNING, CRITICAL_OVERLOAD")
    active_chargers_count: int = Field(..., description="Count of chargers actively drawing current")
    faulted_chargers_count: int = Field(..., description="Count of chargers in FAULT state")
    chargers: List[ChargerFleetSummary] = Field(..., description="Per-charger snapshot at this time slice")


class FleetScenario(BaseModel):
    fleet_scenario_id: str = Field(..., description="Unique fleet scenario identifier")
    name: str = Field(..., description="Human-readable scenario title")
    description: str = Field(..., description="Detailed description of fleet setup and simulated event")
    charger_count: int = Field(default=20, ge=10, le=50, description="Number of simulated chargers in the fleet (10-50)")
    duration_seconds: float = Field(default=60.0, ge=5.0, le=300.0, description="Simulation duration in seconds")
    seed: int = Field(default=42, ge=0, description="Deterministic random seed")
    feeder_config: FeederConfig = Field(default_factory=FeederConfig, description="Feeder capacity and voltage configuration")
    events: List[Dict[str, Any]] = Field(default_factory=list, description="Scheduled cyber events targeting specific chargers or the fleet")
    enabled_defenses: List[str] = Field(default_factory=list, description="Active simulated mitigations for this fleet run")


class FleetSimulationRun(BaseModel):
    run_id: str = Field(..., description="Unique fleet execution ID")
    fleet_scenario_id: str = Field(..., description="Source fleet scenario identifier")
    charger_count: int = Field(..., description="Total simulated chargers")
    feeder_capacity_kw: float = Field(..., description="Configured feeder capacity in kW")
    peak_fleet_power_kw: float = Field(..., description="Maximum total active power recorded during run")
    peak_feeder_loading_pct: float = Field(..., description="Maximum feeder loading recorded during run")
    min_feeder_voltage_v: float = Field(..., description="Minimum feeder voltage recorded under peak load")
    overload_duration_seconds: float = Field(..., description="Total duration feeder exceeded warning/critical threshold")
    affected_chargers: List[str] = Field(default_factory=list, description="List of charger IDs affected by cyber events or faults")
    time_slices: List[FleetTimeSlice] = Field(..., description="Chronological time-series snapshots")
    summary: Dict[str, Any] = Field(default_factory=dict, description="Metadata and high-level evaluation metrics")
