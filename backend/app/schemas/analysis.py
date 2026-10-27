"""
Analysis and Counterfactual Schemas (Features F21, F22, F24, F26, F27, F29, F41).
Defines correlation links, rule evaluations, confidence breakdown, impact severity,
explainable event classification, and investigator checklists.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum


class EvidenceLabel(str, Enum):
    OBSERVED = "Observed"
    INFERRED = "Inferred"
    UNCERTAIN = "Uncertain"


class EventCategory(str, Enum):
    ATTACK_LIKE = "Attack-like simulated event"
    SENSOR_FAULT = "Sensor fault"
    BENIGN_HIGH_POWER = "Benign high-power event"
    UNCERTAIN = "Uncertain"


class SeverityLevel(str, Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"


class ConfidenceBreakdown(BaseModel):
    path_validity_score: float = Field(..., ge=0.0, le=1.0, description="NetworkX path reachability (weight: 0.25)")
    timing_fit_score: float = Field(..., ge=0.0, le=1.0, description="Arrival within physical latency window (weight: 0.20)")
    physics_consistency_score: float = Field(..., ge=0.0, le=1.0, description="Agreement between reported and predicted thermal physics (weight: 0.20)")
    counterfactual_score: float = Field(..., ge=0.0, le=1.0, description="Effect attenuation when event was omitted (weight: 0.20)")
    command_provenance_score: float = Field(..., ge=0.0, le=1.0, description="Authorization / signature provenance score (weight: 0.15)")
    alternative_explanation_penalty: float = Field(default=0.0, le=0.0, description="Negative adjustment for co-occurring benign factors")
    final_score: float = Field(..., ge=0.0, le=1.0, description="Normalized composite confidence score")
    confidence_level: str = Field(..., description="Categorical rating: Low (<0.50), Medium (0.50-0.75), High (>=0.75)")
    scoring_notes: str = Field(..., description="Documented weighting rationale (initial design setting, uncalibrated probability)")


class ImpactSeverity(BaseModel):
    severity_level: SeverityLevel = Field(..., description="Low, Medium, High, Critical")
    peak_current_observed: float
    peak_temp_observed: float
    distance_to_critical_temp_c: float
    rate_of_temp_rise_c_per_min: float
    abnormal_duration_seconds: float
    components_affected_count: int
    protection_tripped: bool
    explanation: str
    limitations: str = Field(
        default="Severity levels represent illustrative model thresholds and digital twin state limits, not certified electrical ratings."
    )


class ClassificationResult(BaseModel):
    event_id: str
    classification: EventCategory
    confidence: float
    supporting_clues: List[str] = Field(default_factory=list)
    conflicting_clues: List[str] = Field(default_factory=list)
    uncertainty_explanation: str
    evaluated_without_ground_truth: bool = True


class InvestigatorItem(BaseModel):
    step_number: int
    recommendation: str
    reason: str
    supporting_evidence_id: Optional[str] = None
    target_component: Optional[str] = None
    status: str = "pending"  # "pending", "verified", "inconclusive"


class InvestigatorGuidance(BaseModel):
    run_id: str
    incident_summary: str
    suggested_steps: List[InvestigatorItem] = Field(default_factory=list)
    disclaimer: str = Field(
        default="Guidance represents a structured rule-based checklist for research investigation. It does not establish legal attribution or replace human SOC oversight."
    )


class CorrelationLink(BaseModel):
    link_id: str = Field(..., description="Unique link identifier")
    event_id: str = Field(..., description="Linked simulated event ID")
    event_type: str = Field(..., description="Type of cyber/control event")
    source: str = Field(..., description="Source of the event")
    target_signal: str = Field(..., description="Affected physical telemetry signal")
    target_component: str = Field(..., description="Physical component affected")
    dependency_path: List[str] = Field(..., description="Validated causal path in component graph")
    time_delay: float = Field(..., description="Measured latency from event to physical response in seconds")
    observed_change: float = Field(..., description="Magnitude of physical change detected")
    change_unit: str = Field(..., description="Unit of change (°C, A, V, %)")
    confidence_score: float = Field(..., description="Confidence score between 0.0 and 1.0")
    evidence_label: EvidenceLabel = Field(..., description="Observed, Inferred, or Uncertain")
    rules_matched: List[str] = Field(..., description="List of rule IDs / names satisfied")
    explanation: str = Field(..., description="Human-readable causal explanation")
    uncertainty_notes: Optional[str] = Field(None, description="Caveats or alternative hypotheses considered")

    # Tier 2 Advanced Additions
    confidence_breakdown: Optional[ConfidenceBreakdown] = None
    impact_severity: Optional[ImpactSeverity] = None
    event_classification: Optional[ClassificationResult] = None
    aligned_time_delay: Optional[float] = None


class CounterfactualRequest(BaseModel):
    target_event_id: str = Field(..., description="The specific simulated event ID to remove for counterfactual replay")


class CounterfactualOverlayPoint(BaseModel):
    timestamp: float
    original_temperature: float
    replay_temperature: float
    original_current: float
    replay_current: float
    original_voltage: float
    replay_voltage: float
    original_soc: float
    replay_soc: float


class CounterfactualResponse(BaseModel):
    original_run_id: str
    counterfactual_run_id: str
    target_event_id: str
    seed_used: int
    peak_current_diff: float = Field(..., description="Original peak current minus replay peak current (A)")
    peak_temp_diff: float = Field(..., description="Original peak temperature minus replay peak temperature (°C)")
    final_soc_diff: float = Field(..., description="Original final SoC minus replay final SoC (%)")
    effect_attribution: str = Field(..., description="DISAPPEARED, DECREASED, or UNCHANGED")
    is_causally_proven: bool = Field(..., description="True if removing the event proved elimination or major reduction of physical impact")
    summary: str = Field(..., description="Detailed counterfactual finding summary")
    limitations: str = Field(..., description="Explicit scientific caveats of the simulation replay")
    overlay_data: List[CounterfactualOverlayPoint] = Field(default_factory=list)
