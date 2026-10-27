"""
Evaluation and Benchmarking Schemas (Features F44, F45, F46).
Covers precision, recall, false-link rate, detection latency vs physical delay, and held-out validation.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any


class MetricComparison(BaseModel):
    threatlens_value: float
    baseline_60s_spike_value: float
    differential: float
    unit: str
    interpretation: str


class EvaluationScorecardResponse(BaseModel):
    evaluation_id: str
    split_name: str  # "tuning" or "held_out"
    total_scenarios_evaluated: int
    total_candidate_events: int
    true_positive_links: int
    false_positive_links: int
    false_negative_links: int
    true_negative_links: int
    
    # Core Metrics
    precision: float
    recall: float
    f1_score: float
    false_link_rate: float
    classification_accuracy: float
    counterfactual_agreement: float

    # Comparison against 60-second heuristic baseline
    baseline_comparison: Dict[str, MetricComparison]

    # Latency Metrics
    avg_physical_delay_seconds: float
    avg_software_computation_ms: float
    p95_software_computation_ms: float
    latency_distinction_notes: str

    evaluated_scenarios: List[str]
    methodology_notes: str
    reproducibility_seed: int
