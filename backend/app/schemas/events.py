"""
Standard Event Schema (Feature F16).
Provides consistent event representation across simulation, analysis, persistence, and UI.
"""

from pydantic import BaseModel, Field
from typing import Dict, Any, Optional


class GroundTruthMetadata(BaseModel):
    is_malicious: bool = False
    target_signal: Optional[str] = None
    expected_delta: Optional[str] = None
    expected_causal: bool = False
    rationale: Optional[str] = None


class SimulatedEventSchema(BaseModel):
    event_id: str = Field(..., description="Unique event identifier (e.g. EVT-001)")
    timestamp: float = Field(..., description="Time of event occurrence in seconds from start")
    layer: str = Field(..., description="Architecture layer: cyber_protocol, controller, hardware, sensor, grid")
    component_id: str = Field(..., description="Component generating or receiving the event")
    event_type: str = Field(..., description="Predefined event type (e.g. CHANGE_CURRENT_LIMIT)")
    source: str = Field(..., description="Origin of event: csms, operator, local_attacker, etc.")
    auth_status: str = Field(..., description="Authentication status: authorized, unauthorized, spoofed, bypassed")
    description: Optional[str] = Field(default=None, description="Human-readable event description")
    details: Dict[str, Any] = Field(default_factory=dict, description="Event payload parameters")
    ground_truth: Optional[GroundTruthMetadata] = Field(default=None, description="Scenario benchmark ground-truth annotation")
