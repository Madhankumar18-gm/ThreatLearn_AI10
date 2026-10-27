"""
ThreatLens OCPP Gateway Schemas.
Pydantic contracts for Gateway status, configuration, interventions, and scenario execution.
"""

from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional


class GatewayMetrics(BaseModel):
    total_messages: int = 0
    allowed: int = 0
    clamped: int = 0
    blocked: int = 0
    errors: int = 0


class GatewayAuditMetrics(BaseModel):
    total_events: int = 0
    delivered_events: int = 0
    dropped_events: int = 0
    queue_capacity: int = 1000
    queue_depth: int = 0


class GatewayPolicyConfigSchema(BaseModel):
    current_cap_enabled: bool = True
    current_cap_value: float = Field(default=100.0, ge=10.0, le=250.0)
    hardware_max_current: float = Field(default=150.0, ge=50.0, le=300.0)
    rate_limiting_enabled: bool = True
    min_command_interval_seconds: float = Field(default=5.0, ge=0.5, le=60.0)
    auth_validation_enabled: bool = True
    thermal_lockout_enabled: bool = True
    thermal_lockout_threshold_c: float = Field(default=45.0, ge=30.0, le=90.0)


class GatewayStatusResponse(BaseModel):
    state: str  # "STOPPED", "STARTING", "RUNNING", "ERROR"
    is_running: bool
    host: str = "127.0.0.1"
    charger_port: int = 9000
    csms_port: int = 9001
    uptime_seconds: float = 0.0
    active_sessions: int = 0
    metrics: GatewayMetrics = Field(default_factory=GatewayMetrics)
    policy: GatewayPolicyConfigSchema = Field(default_factory=GatewayPolicyConfigSchema)
    audit: GatewayAuditMetrics = Field(default_factory=GatewayAuditMetrics)
    disclaimer: str


class GatewayStartRequest(BaseModel):
    charger_port: Optional[int] = Field(default=9000, ge=1024, le=65535)
    csms_port: Optional[int] = Field(default=9001, ge=1024, le=65535)
    start_mock_csms: bool = True


class GatewayPolicyUpdateRequest(BaseModel):
    current_cap_enabled: Optional[bool] = None
    current_cap_value: Optional[float] = None
    rate_limiting_enabled: Optional[bool] = None
    min_command_interval_seconds: Optional[float] = None
    auth_validation_enabled: Optional[bool] = None
    thermal_lockout_enabled: Optional[bool] = None
    thermal_lockout_threshold_c: Optional[float] = None


class GatewayInterventionRecord(BaseModel):
    timestamp: float
    charge_point_id: str
    unique_id: str
    action: str
    direction: str
    decision: str  # "ALLOW", "CLAMP", "BLOCK"
    rule_id: str
    reason: str
    original_limit: Optional[float] = None
    modified_limit: Optional[float] = None
    error_code: Optional[str] = None


class GatewayInterventionsResponse(BaseModel):
    total_records: int
    interventions: List[GatewayInterventionRecord]


class GatewayScenarioCatalogItem(BaseModel):
    id: str
    name: str
    category: str
    description: str
    expected_decisions: List[str]
    threat_actor: str
    mitigation_rule: str


class GatewayScenarioRunRequest(BaseModel):
    scenario_id: str
    charger_id: Optional[str] = "CP_DEMO_01"


class GatewayScenarioRunResponse(BaseModel):
    scenario_id: str
    scenario_name: str
    status: str
    total_messages: int
    decisions: List[Dict[str, Any]]
    charger_received_limit: Optional[float]
    summary: str
    verification_passed: bool
    execution_time_seconds: float
