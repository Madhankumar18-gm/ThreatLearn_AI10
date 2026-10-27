"""
Defense and Mitigation Schemas (Features F39, F40).
Models simulated cyber-physical mitigations and comparative effectiveness analysis.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any


class DefenseConfiguration(BaseModel):
    # Mitigation 1: Command signature / authorization check
    auth_validation_enabled: bool = Field(default=False, description="Rejects unauthorized or spoofed simulated commands")
    # Mitigation 2: Allowed-command whitelist
    command_whitelist_enabled: bool = Field(default=False, description="Rejects commands not in the strict operational whitelist")
    allowed_commands: List[str] = Field(default_factory=lambda: ["START_TRANSACTION", "STOP_TRANSACTION"], description="Approved command types")
    # Mitigation 3: Charging current cap
    current_cap_enabled: bool = Field(default=False, description="Enforces a hard software ceiling on requested charging current")
    current_cap_value: float = Field(default=100.0, description="Max current ceiling in Amperes")
    # Mitigation 4: Command rate limiting
    rate_limiting_enabled: bool = Field(default=False, description="Enforces minimum time between repeated setpoint changes")
    min_interval_seconds: float = Field(default=5.0, description="Minimum interval between commands in seconds")
    # Mitigation 5: Sensor cross-checking
    sensor_crosscheck_enabled: bool = Field(default=False, description="Compares reported sensor readings against model expectations")
    crosscheck_tolerance_c: float = Field(default=3.5, description="Maximum allowed divergence before flagging sensor anomaly (°C)")
    # Mitigation 6: Thermal protection lockout
    thermal_lockout_enabled: bool = Field(default=False, description="Forces persistent trip and halts charging if caution temperature is reached")
    lockout_threshold_c: float = Field(default=45.0, description="Lockout temperature threshold (°C)")


class DefenseIntervention(BaseModel):
    timestamp: float
    mitigation_name: str
    target_event_id: Optional[str] = None
    action_taken: str  # "BLOCKED", "CAPPED", "FLAGGED", "LOCKOUT"
    reason: str
    details: Dict[str, Any] = Field(default_factory=dict)


class DefenseComparisonRequest(BaseModel):
    scenario_id: str
    seed: Optional[int] = None
    defenses: DefenseConfiguration


class DefenseEffectivenessResponse(BaseModel):
    scenario_id: str
    scenario_name: str
    seed_used: int
    defenses_configured: DefenseConfiguration
    interventions_triggered: List[DefenseIntervention] = Field(default_factory=list)
    
    # Baseline run metrics (Defenses OFF)
    baseline_run_id: str
    baseline_peak_temp: float
    baseline_peak_current: float
    baseline_fault_triggered: bool
    baseline_warning_time: Optional[float] = None
    
    # Defended run metrics (Defenses ON)
    defended_run_id: str
    defended_peak_temp: float
    defended_peak_current: float
    defended_fault_triggered: bool
    defended_warning_time: Optional[float] = None
    
    # Differentials & Effectiveness
    temp_reduction_deg_c: float
    current_reduction_a: float
    percent_temp_improvement: float
    is_defense_effective: bool
    summary: str
    limitations: str
