"""
Incident Comparison Engine (Feature F38).
Provides side-by-side comparative analysis of two simulation runs or incident records.
Calculates numerical deltas, evaluates compatibility, and compares defense efficacy.
"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

from backend.app.schemas.simulation import SimulationRunResponse


class MetricDelta(BaseModel):
    metric_name: str
    unit: str
    run_a_value: float
    run_b_value: float
    absolute_delta: float
    percentage_change: float
    better_run: Optional[str] = None
    interpretation: str


class IncidentComparisonResult(BaseModel):
    comparison_id: str
    run_a_id: str
    run_b_id: str
    scenario_a_id: str
    scenario_b_id: str
    is_compatible: bool
    compatibility_warnings: List[str] = Field(default_factory=list)
    metric_deltas: List[MetricDelta] = Field(default_factory=list)
    summary_verdict: str
    run_a_summary: Dict[str, Any]
    run_b_summary: Dict[str, Any]


class IncidentComparator:
    """Compares two incident runs side-by-side with safety delta evaluations."""

    @classmethod
    def compare(
        cls,
        run_a: Dict[str, Any],
        run_b: Dict[str, Any]
    ) -> IncidentComparisonResult:
        import uuid

        run_a_id = run_a.get("run_id", "RUN-A")
        run_b_id = run_b.get("run_id", "RUN-B")
        scn_a = run_a.get("scenario_id", "UNKNOWN")
        scn_b = run_b.get("scenario_id", "UNKNOWN")

        # Compatibility checks
        dur_a = float(run_a.get("duration_seconds", len(run_a.get("telemetry", []))))
        dur_b = float(run_b.get("duration_seconds", len(run_b.get("telemetry", []))))
        warnings = []

        if abs(dur_a - dur_b) > 5.0:
            warnings.append(f"Duration mismatch: Run A ({dur_a:.0f}s) vs Run B ({dur_b:.0f}s). Metrics may reflect unequal integration periods.")

        seed_a = run_a.get("seed")
        seed_b = run_b.get("seed")
        if seed_a != seed_b:
            warnings.append(f"Seeded RNG difference: Run A (seed={seed_a}) vs Run B (seed={seed_b}). Small stochastic noise variance expected.")

        is_compatible = len(warnings) == 0 or (abs(dur_a - dur_b) <= 30.0)

        # Extract peak metrics
        t_peak_a = float(run_a.get("peak_temperature", 25.0))
        t_peak_b = float(run_b.get("peak_temperature", 25.0))
        i_peak_a = float(run_a.get("peak_current", 0.0))
        i_peak_b = float(run_b.get("peak_current", 0.0))
        grid_a = float(run_a.get("peak_grid_load", 0.0))
        grid_b = float(run_b.get("peak_grid_load", 0.0))

        deltas: List[MetricDelta] = []

        # Peak Temperature delta
        dt_temp = t_peak_b - t_peak_a
        pct_temp = round((dt_temp / (t_peak_a if t_peak_a > 0 else 1.0)) * 100.0, 1)
        better_t = run_b_id if t_peak_b < t_peak_a else (run_a_id if t_peak_a < t_peak_b else "TIE")
        deltas.append(
            MetricDelta(
                metric_name="Peak Battery Temperature",
                unit="°C",
                run_a_value=t_peak_a,
                run_b_value=t_peak_b,
                absolute_delta=round(dt_temp, 2),
                percentage_change=pct_temp,
                better_run=better_t,
                interpretation=f"Run B is {abs(dt_temp):.1f}°C {'cooler' if dt_temp < 0 else 'hotter'} than Run A."
            )
        )

        # Peak Current delta
        dt_curr = i_peak_b - i_peak_a
        pct_curr = round((dt_curr / (i_peak_a if i_peak_a > 0 else 1.0)) * 100.0, 1)
        better_i = run_b_id if i_peak_b < i_peak_a else (run_a_id if i_peak_a < i_peak_b else "TIE")
        deltas.append(
            MetricDelta(
                metric_name="Peak Charging Current",
                unit="A",
                run_a_value=i_peak_a,
                run_b_value=i_peak_b,
                absolute_delta=round(dt_curr, 2),
                percentage_change=pct_curr,
                better_run=better_i,
                interpretation=f"Run B experienced {abs(dt_curr):.1f}A {'less' if dt_curr < 0 else 'more'} peak current than Run A."
            )
        )

        # Peak Grid Load delta
        dt_grid = grid_b - grid_a
        pct_grid = round((dt_grid / (grid_a if grid_a > 0 else 1.0)) * 100.0, 1)
        deltas.append(
            MetricDelta(
                metric_name="Peak Electrical Load",
                unit="kW",
                run_a_value=grid_a,
                run_b_value=grid_b,
                absolute_delta=round(dt_grid, 2),
                percentage_change=pct_grid,
                better_run=run_b_id if grid_b < grid_a else run_a_id,
                interpretation=f"Run B drew {abs(dt_grid):.1f} kW {'less' if dt_grid < 0 else 'more'} peak power."
            )
        )

        # High level comparative summary
        trips_a = run_a.get("safety_trip_occurred", False)
        trips_b = run_b.get("safety_trip_occurred", False)

        if trips_a and not trips_b:
            verdict = f"{run_b_id} successfully mitigated safety trips that occurred in {run_a_id}."
        elif dt_temp < -5.0:
            verdict = f"{run_b_id} demonstrated substantial thermal reduction (-{abs(dt_temp):.1f}°C) compared to {run_a_id}."
        elif dt_temp > 5.0:
            verdict = f"{run_a_id} exhibited safer thermal margins than {run_b_id} (+{dt_temp:.1f}°C higher in B)."
        else:
            verdict = f"Both runs exhibited comparable cyber-physical performance (ΔT = {dt_temp:.1f}°C)."

        return IncidentComparisonResult(
            comparison_id=f"CMP-{uuid.uuid4().hex[:8].upper()}",
            run_a_id=run_a_id,
            run_b_id=run_b_id,
            scenario_a_id=scn_a,
            scenario_b_id=scn_b,
            is_compatible=is_compatible,
            compatibility_warnings=warnings,
            metric_deltas=deltas,
            summary_verdict=verdict,
            run_a_summary={
                "peak_temperature": t_peak_a,
                "peak_current": i_peak_a,
                "tripped": trips_a,
                "classification": run_a.get("classification", "Unknown"),
                "severity": run_a.get("severity", "Unknown")
            },
            run_b_summary={
                "peak_temperature": t_peak_b,
                "peak_current": i_peak_b,
                "tripped": trips_b,
                "classification": run_b.get("classification", "Unknown"),
                "severity": run_b.get("severity", "Unknown")
            }
        )
