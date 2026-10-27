"""
Standard Telemetry Schema (Features F11, F13, F16, F19, F23).
Provides consistent time-series sensor/model telemetry across simulation, analysis, and UI.
Distinguishes true physical states from reported sensor measurements and digital twin predictions.
"""

from pydantic import BaseModel, Field
from typing import Optional, List


class TelemetryPoint(BaseModel):
    timestamp: float = Field(..., description="Timestamp in seconds from simulation start")
    component_id: str = Field(..., description="Component emitting telemetry")
    signal: str = Field(..., description="Physical signal name (battery_temperature, charging_current, etc.)")
    value: float = Field(..., description="Measured or simulated scalar value")
    unit: str = Field(..., description="Engineering unit (°C, A, V, %, kW)")
    quality: str = Field(default="good", description="Signal quality: good, suspect, fault, dropout")


class TelemetryTimeSlice(BaseModel):
    """Aggregated slice for multi-signal frontend plotting and residual analysis at time t."""
    timestamp: float
    aligned_timestamp: Optional[float] = None
    
    # Physical states (ground truth physics)
    battery_temperature: float
    charging_current: float
    battery_voltage: float
    state_of_charge: float
    cooling_power: float
    grid_load: float
    charger_state: str

    # Reported sensor measurements (may suffer drift, stuck, spikes, or noise)
    sensor_temperature: Optional[float] = None
    reported_current: Optional[float] = None
    sensor_quality: str = Field(default="good", description="Sensor quality flag: good, suspect, fault, dropout")

    # Digital twin physics consistency prediction (Feature F23)
    predicted_temperature: Optional[float] = None
    temperature_residual: Optional[float] = None  # reported - predicted

    # CAN-style in-vehicle simulated spoofed signals (Feature F13)
    can_spoofed_temperature: Optional[float] = None
    can_spoofed_current: Optional[float] = None
