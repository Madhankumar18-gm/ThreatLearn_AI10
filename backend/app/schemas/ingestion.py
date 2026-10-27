"""
Ingestion and Time Alignment Schemas (Features F17, F19).
Supports CSV upload, schema preview, canonical mapping, validation, and clock alignment.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any


class CSVColumnMapping(BaseModel):
    timestamp_col: str
    component_col: Optional[str] = None
    event_type_col: Optional[str] = None
    signal_col: Optional[str] = None
    value_col: Optional[str] = None
    unit_col: Optional[str] = None
    quality_col: Optional[str] = None
    auth_status_col: Optional[str] = None
    source_col: Optional[str] = None


class CSVPreviewResponse(BaseModel):
    filename: str
    total_rows: int
    headers: List[str]
    sample_rows: List[Dict[str, Any]]
    inferred_mapping: CSVColumnMapping
    detected_data_type: str  # "events", "telemetry", or "mixed"
    time_format: Optional[str] = "relative_seconds"  # "iso8601", "relative_seconds", or "epoch"
    base_timestamp: Optional[str] = None
    duration_seconds: Optional[float] = None


class IngestionCommitRequest(BaseModel):
    filename: str
    data_type: str = "telemetry"  # "events", "telemetry", or "mixed"
    mapping: CSVColumnMapping
    rows: Optional[List[Dict[str, Any]]] = None
    raw_content: Optional[str] = None
    clock_skew_offset: float = Field(default=0.0, description="Manual clock offset in seconds (t_aligned = t_orig + offset)")


class RowRejection(BaseModel):
    row_index: int
    reason: str
    raw_value: Optional[str] = None
    column: Optional[str] = None


class IngestionValidationReport(BaseModel):
    dataset_id: str
    total_submitted: int
    valid_rows_count: int
    rejected_rows_count: int
    warnings: List[str] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)
    rejections: List[RowRejection] = Field(default_factory=list)
    aligned_time_range: Dict[str, Any]


class TimeAlignmentRequest(BaseModel):
    run_id: str
    clock_offset_seconds: float = Field(..., description="Clock offset to apply to cyber events (seconds)")
    marker_event_id: Optional[str] = Field(None, description="Optional marker event ID to anchor alignment")
    marker_signal_timestamp: Optional[float] = Field(None, description="Optional telemetry timestamp corresponding to marker event")


class TimeAlignmentResponse(BaseModel):
    run_id: str
    applied_offset_seconds: float
    alignment_method: str  # "manual_offset" or "marker_anchored"
    original_event_count: int
    aligned_events: List[Dict[str, Any]]
    estimated_uncertainty_seconds: float
    correlation_window_adjusted: bool
    explanation: str
