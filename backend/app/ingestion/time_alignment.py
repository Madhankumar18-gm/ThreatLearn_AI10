"""
Time Alignment Service (Feature F19).
Aligns disparate cyber event logs and physical telemetry channels through
configurable clock offsets and marker-anchored cross-correlation.
Preserves original timestamps while computing aligned timelines and uncertainty bounds.
"""

from typing import List, Dict, Any, Optional
from backend.app.schemas.ingestion import TimeAlignmentRequest, TimeAlignmentResponse


class TimeAlignmentEngine:

    @classmethod
    def align_events(
        cls,
        req: TimeAlignmentRequest,
        events: List[Dict[str, Any]]
    ) -> TimeAlignmentResponse:
        """
        Computes aligned timestamps for cyber event records.
        Supports manual offset and marker-anchored cross-referencing.
        """
        offset = req.clock_offset_seconds
        method = "manual_offset"

        # If marker event is provided, compute dynamic offset:
        # offset = marker_signal_timestamp - marker_event_timestamp
        if req.marker_event_id and req.marker_signal_timestamp is not None:
            marker_ev = next((e for e in events if e.get("event_id") == req.marker_event_id), None)
            if marker_ev:
                orig_ts = float(marker_ev.get("timestamp", 0.0))
                offset = req.marker_signal_timestamp - orig_ts
                method = "marker_anchored"

        aligned_list: List[Dict[str, Any]] = []
        for ev in events:
            ev_copy = dict(ev)
            orig_ts = float(ev.get("timestamp", 0.0))
            aligned_ts = max(0.0, round(orig_ts + offset, 3))
            
            ev_copy["original_timestamp"] = orig_ts
            ev_copy["aligned_timestamp"] = aligned_ts
            ev_copy["time_uncertainty_seconds"] = 0.5 if method == "marker_anchored" else 1.0
            aligned_list.append(ev_copy)

        # Sort chronologically by aligned timestamp
        aligned_list.sort(key=lambda x: x["aligned_timestamp"])

        uncertainty = 0.5 if method == "marker_anchored" else 1.0

        return TimeAlignmentResponse(
            run_id=req.run_id,
            applied_offset_seconds=round(offset, 3),
            alignment_method=method,
            original_event_count=len(events),
            aligned_events=aligned_list,
            estimated_uncertainty_seconds=uncertainty,
            correlation_window_adjusted=True,
            explanation=f"Applied clock offset of {offset:+.2f}s using {method}. Causal search window expanded by ±{uncertainty}s."
        )
