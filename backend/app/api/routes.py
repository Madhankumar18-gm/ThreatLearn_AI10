"""
FastAPI REST API Routes (Features F01-F50).
Exposes endpoints for:
- Scenario library querying & custom scenario builder (F01, F02)
- Scenario JSON import & export (F05)
- Deterministic simulation with noise, clock skew, & active defenses (F03, F04, F06-F16, F39)
- CSV / Log ingestion wizard & preview (F17)
- Clock skew & marker time alignment (F19)
- Rule-based causal correlation & physics consistency (F21, F23, F24, F26, F27, F29)
- Deterministic counterfactual replay (F22, F32)
- Defense Lab comparative evaluation (F39, F40)
- Investigator guidance checklist (F41)
- Benchmark scorecard & held-out evaluation (F44, F45, F46)
- Dependency topology graph export (F20)
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional

from backend.app.database.session import get_db
from backend.app.database.repository import Repository
from backend.app.schemas.scenario import ScenarioSchema, ScenarioCreateRequest
from backend.app.schemas.simulation import (
    SimulationRunRequest, SimulationRunResponse, RunSummary
)
from backend.app.schemas.analysis import (
    CorrelationLink, CounterfactualRequest, CounterfactualResponse, InvestigatorGuidance,
    ImpactAnalysisReport
)
from backend.app.schemas.defense import (
    DefenseConfiguration, DefenseComparisonRequest, DefenseEffectivenessResponse
)
from backend.app.schemas.ingestion import (
    CSVPreviewResponse, IngestionCommitRequest, IngestionValidationReport,
    TimeAlignmentRequest, TimeAlignmentResponse
)
from backend.app.schemas.evaluation import EvaluationScorecardResponse
from backend.app.schemas.fleet import FleetScenario, FleetSimulationRun, FeederConfig

from backend.app.scenarios.library import SCENARIOS_MAP
from backend.app.scenarios.builder import ScenarioBuilder
from backend.app.scenarios.import_export import ScenarioImportExport
from backend.app.simulation.simulator import SimulationEngine
from backend.app.simulation.fleet_simulator import FleetSimulationEngine
from backend.app.core.taxonomy import EventTaxonomyCatalog
from backend.app.ingestion.csv_importer import CSVImporter
from backend.app.ingestion.time_alignment import TimeAlignmentEngine
from backend.app.ingestion.public_dataset_adapter import PublicDatasetAdapter
from backend.app.analysis.correlation_engine import CorrelationEngine
from backend.app.analysis.counterfactual import CounterfactualEngine
from backend.app.analysis.consistency_checker import PhysicsConsistencyChecker
from backend.app.analysis.masked_attack import MaskedAttackDetector
from backend.app.analysis.anomaly_detector import AnomalyDetectionAssistant
from backend.app.analysis.incident_comparison import IncidentComparator
from backend.app.analysis.narrative import NarrativeGenerator
from backend.app.analysis.investigator import InvestigatorGuidanceEngine
from backend.app.analysis.evaluation import EvaluationEngine
from backend.app.analysis.ablation import AblationEngine
from backend.app.reports.report_generator import ReportGenerator
from backend.app.analysis.dependency_graph import dependency_graph
from backend.app.analysis.impact_analysis import ImpactAnalysisEngine
from backend.app.core.config import settings

router = APIRouter()


@router.get("/health", summary="Service Health and Status")
def get_health():
    """Returns application status, version, and simulation mode badge confirmation."""
    return {
        "status": "healthy",
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "simulation_mode": settings.SIMULATION_MODE_ENABLED,
        "total_scenarios": len(SCENARIOS_MAP)
    }


# =========================================================================
# SCENARIOS & BUILDER (F01, F02, F05)
# =========================================================================

@router.get("/scenarios", response_model=List[ScenarioSchema], summary="List All Scenarios (F01)")
def list_scenarios(
    family: Optional[str] = Query(None, description="Filter by scenario family"),
    db: Session = Depends(get_db)
):
    """Returns the library of labelled deterministic scenarios."""
    scenarios = list(SCENARIOS_MAP.values())
    if family:
        scenarios = [s for s in scenarios if s.family.lower() == family.lower()]
    return scenarios


@router.get("/scenarios/{scenario_id}", response_model=ScenarioSchema, summary="Get Scenario by ID")
def get_scenario(scenario_id: str):
    """Retrieves full specification for a single scenario."""
    if scenario_id not in SCENARIOS_MAP:
        raise HTTPException(status_code=404, detail=f"Scenario '{scenario_id}' not found.")
    return SCENARIOS_MAP[scenario_id]


@router.post("/scenarios/custom", response_model=ScenarioSchema, summary="Build Custom Scenario (F02)")
def create_custom_scenario(req: ScenarioCreateRequest, db: Session = Depends(get_db)):
    """Validates parameters, whitelists events, and creates a safe custom scenario."""
    try:
        scenario = ScenarioBuilder.build_custom_scenario(req)
        SCENARIOS_MAP[scenario.scenario_id] = scenario
        Repository.save_scenario(db, scenario)
        return scenario
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create scenario: {str(e)}")


@router.get("/scenarios/{scenario_id}/export", summary="Export Scenario JSON (F05)")
def export_scenario(scenario_id: str):
    """Serializes a scenario to versioned JSON envelope."""
    if scenario_id not in SCENARIOS_MAP:
        raise HTTPException(status_code=404, detail=f"Scenario '{scenario_id}' not found.")
    scenario = SCENARIOS_MAP[scenario_id]
    return ScenarioImportExport.export_scenario(scenario)


@router.post("/scenarios/import", summary="Import Scenario JSON (F05)")
def import_scenario(payload: Dict[str, Any], db: Session = Depends(get_db)):
    """Validates, assigns a safe identifier prefix, and imports an external scenario definition."""
    try:
        scenario, msg = ScenarioImportExport.import_scenario(payload)
        SCENARIOS_MAP[scenario.scenario_id] = scenario
        Repository.save_scenario(db, scenario)
        return {"message": msg, "scenario": scenario}
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to import scenario: {str(e)}")


# =========================================================================
# SIMULATION EXECUTION & PERSISTENCE (F03, F04, F06-F16, F51)
# =========================================================================

@router.post("/runs", response_model=SimulationRunResponse, summary="Execute Deterministic Simulation")
def create_run(request: SimulationRunRequest, db: Session = Depends(get_db)):
    """
    Executes a deterministic simulation of an EV charging session under the specified scenario.
    Applies configurable noise, clock skew, and active defenses.
    """
    if request.scenario_id not in SCENARIOS_MAP:
        raise HTTPException(status_code=404, detail=f"Scenario '{request.scenario_id}' not found.")

    scenario = SCENARIOS_MAP[request.scenario_id]

    try:
        run_result = SimulationEngine.run(
            scenario=scenario,
            seed=request.seed,
            omitted_event_id=request.omitted_event_id,
            custom_defenses=request.custom_defenses,
            cyber_offset_override=request.cyber_timestamp_offset,
            telemetry_offset_override=request.telemetry_timestamp_offset,
            sensor_noise_override=request.sensor_noise_std
        )

        # Persist run to SQLite
        Repository.save_run(db, run_result)

        # Run correlation engine on results
        correlation_links = CorrelationEngine.analyze_run(run_result)
        Repository.save_correlation_links(db, run_result.run_id, correlation_links)

        return run_result

    except ValueError as val_err:
        raise HTTPException(status_code=400, detail=str(val_err))
    except Exception as err:
        raise HTTPException(status_code=500, detail=f"Simulation execution failed: {str(err)}")


@router.get("/runs", response_model=List[RunSummary], summary="List Simulation Incident History (F51)")
def list_runs(limit: int = 50, db: Session = Depends(get_db)):
    """Retrieves saved simulation runs from SQLite database."""
    return Repository.get_runs(db, limit=limit)


@router.get("/runs/{run_id}", response_model=SimulationRunResponse, summary="Get Full Simulation Run Details")
def get_run(run_id: str, db: Session = Depends(get_db)):
    """Retrieves full telemetry, events, and threshold crossings for a saved incident."""
    run = Repository.get_run(db, run_id)
    if not run:
        raise HTTPException(status_code=404, detail=f"Run '{run_id}' not found.")
    return run


@router.get("/runs/{run_id}/links", response_model=List[CorrelationLink], summary="Get Correlated Links (F21, F29)")
def get_run_links(run_id: str, db: Session = Depends(get_db)):
    """Retrieves explainable rule-based correlation links with dependency paths and evidence labels."""
    run = Repository.get_run(db, run_id)
    if not run:
        raise HTTPException(status_code=404, detail=f"Run '{run_id}' not found.")

    links = Repository.get_correlation_links(db, run_id)
    if not links:
        links = CorrelationEngine.analyze_run(run)
        Repository.save_correlation_links(db, run_id, links)
    return links


@router.get("/runs/{run_id}/impact-analysis", response_model=ImpactAnalysisReport, summary="Get Cyber-to-Physical Impact Analysis")
def get_impact_analysis(
    run_id: str,
    baseline_run_id: Optional[str] = Query(default=None, description="Optional baseline run for comparative delta"),
    feeder_capacity_kw: float = Query(default=800.0, description="Rated feeder capacity in kW"),
    feeder_nominal_voltage_v: float = Query(default=400.0, description="Distribution nominal AC voltage"),
    db: Session = Depends(get_db)
):
    """
    Computes rigorous cyber-to-physical impact chain, quantitative metrics,
    feeder loading & voltage sag, threshold crossings, and correlated gateway interventions.
    """
    run = Repository.get_run(db, run_id)
    if not run:
        raise HTTPException(status_code=404, detail=f"Run '{run_id}' not found.")

    baseline_run = None
    if baseline_run_id:
        baseline_run = Repository.get_run(db, baseline_run_id)

    report = ImpactAnalysisEngine.analyze_run(
        run=run,
        baseline_run=baseline_run,
        feeder_capacity_kw=feeder_capacity_kw,
        feeder_nominal_voltage_v=feeder_nominal_voltage_v,
    )
    return report


@router.post("/runs/{run_id}/counterfactual", response_model=CounterfactualResponse, summary="Execute Counterfactual Replay (F22, F32)")
def run_counterfactual(
    run_id: str,
    request: CounterfactualRequest,
    db: Session = Depends(get_db)
):
    """
    Reruns the scenario under identical seed and conditions, removing only the target event.
    Proves or disproves causal cyber-to-physical attribution.
    """
    orig_run = Repository.get_run(db, run_id)
    if not orig_run:
        raise HTTPException(status_code=404, detail=f"Run '{run_id}' not found.")

    if orig_run.scenario_id not in SCENARIOS_MAP:
        raise HTTPException(status_code=404, detail=f"Scenario '{orig_run.scenario_id}' not found in library.")

    scenario = SCENARIOS_MAP[orig_run.scenario_id]

    matching_events = [e for e in orig_run.events if e.event_id == request.target_event_id]
    if not matching_events:
        raise HTTPException(
            status_code=400,
            detail=f"Target event '{request.target_event_id}' does not exist in run '{run_id}'."
        )

    try:
        cf_response = CounterfactualEngine.run_replay(
            original_run=orig_run,
            scenario=scenario,
            target_event_id=request.target_event_id
        )
        Repository.save_counterfactual_replay(db, cf_response)
        return cf_response

    except Exception as err:
        raise HTTPException(status_code=500, detail=f"Counterfactual replay execution failed: {str(err)}")


# =========================================================================
# CSV & LOG INGESTION WIZARD (F17, F19)
# =========================================================================

@router.post("/ingest/preview", response_model=CSVPreviewResponse, summary="Preview CSV Upload (F17)")
def preview_csv_upload(payload: Dict[str, str]):
    """Parses uploaded CSV string, detects headers, infers column mapping, and returns preview."""
    filename = payload.get("filename", "upload.csv")
    content = payload.get("content", "")
    if not content.strip():
        raise HTTPException(status_code=400, detail="Uploaded CSV content cannot be empty.")
    try:
        return CSVImporter.preview_csv(filename, content)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"CSV parse error: {str(e)}")


@router.post("/ingest/commit", response_model=IngestionValidationReport, summary="Commit and Validate Ingestion (F17)")
def commit_ingestion(req: IngestionCommitRequest):
    """Validates user-mapped rows, applies clock offset, and checks numerical bounds."""
    try:
        report, _ = CSVImporter.validate_and_commit(req)
        return report
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Ingestion commit error: {str(e)}")


@router.get("/ingest/datasets", summary="List Ingested Datasets (F17)")
def list_ingested_datasets():
    """Returns list of committed ingested datasets."""
    return CSVImporter.list_datasets()


@router.get("/ingest/datasets/{dataset_id}", summary="Get Ingested Dataset Details (F17)")
def get_ingested_dataset(dataset_id: str):
    """Retrieves full record of committed dataset by ID."""
    ds = CSVImporter.get_dataset(dataset_id)
    if not ds:
        raise HTTPException(status_code=404, detail=f"Dataset '{dataset_id}' not found.")
    return ds


@router.post("/align", response_model=TimeAlignmentResponse, summary="Align Event Clock Skew (F19)")
def align_run_timestamps(req: TimeAlignmentRequest, db: Session = Depends(get_db)):
    """Applies clock offset to event logs, displaying aligned timelines and uncertainty bounds."""
    run = Repository.get_run(db, req.run_id)
    if not run:
        raise HTTPException(status_code=404, detail=f"Run '{req.run_id}' not found.")
    raw_events = [e.model_dump() for e in run.events]
    return TimeAlignmentEngine.align_events(req, raw_events)


# =========================================================================
# DEFENSE LAB COMPARISON (F39, F40)
# =========================================================================

@router.post("/defense/compare", response_model=DefenseEffectivenessResponse, summary="Compare Baseline vs Defended Run (F39, F40)")
def compare_defenses(req: DefenseComparisonRequest, db: Session = Depends(get_db)):
    """
    Executes identical scenario twice: once with defenses disabled, once with defenses active.
    Returns comparative before/after metrics, thermal delta, and interventions.
    """
    if req.scenario_id not in SCENARIOS_MAP:
        raise HTTPException(status_code=404, detail=f"Scenario '{req.scenario_id}' not found.")
    scenario = SCENARIOS_MAP[req.scenario_id]
    seed_used = req.seed if req.seed is not None else scenario.default_seed

    # 1. Baseline run (defenses completely disabled)
    baseline_run = SimulationEngine.run(
        scenario=scenario,
        seed=seed_used,
        custom_defenses=DefenseConfiguration()
    )
    Repository.save_run(db, baseline_run)

    # 2. Defended run (with user-specified defense configuration)
    defended_run = SimulationEngine.run(
        scenario=scenario,
        seed=seed_used,
        custom_defenses=req.defenses
    )
    Repository.save_run(db, defended_run)

    # 3. Compute effectiveness metrics
    temp_reduct = round(max(0.0, baseline_run.peak_temperature - defended_run.peak_temperature), 2)
    curr_reduct = round(max(0.0, baseline_run.peak_current - defended_run.peak_current), 2)
    pct_imp = round((temp_reduct / max(1.0, baseline_run.peak_temperature - settings.AMBIENT_TEMPERATURE)) * 100.0, 1) if baseline_run.peak_temperature > settings.AMBIENT_TEMPERATURE else 0.0

    is_effective = (
        (baseline_run.fault_triggered and not defended_run.fault_triggered) or
        temp_reduct >= 2.0 or
        curr_reduct >= 15.0 or
        len(defended_run.defense_interventions) > 0
    )

    summary = (
        f"Defenses triggered {len(defended_run.defense_interventions)} active interventions. "
        f"Peak temperature lowered from {baseline_run.peak_temperature:.1f}°C to {defended_run.peak_temperature:.1f}°C (-{temp_reduct:.1f}°C). "
        f"{'Hardware safety breaker trip prevented! ' if (baseline_run.fault_triggered and not defended_run.fault_triggered) else ''}"
    )

    return DefenseEffectivenessResponse(
        scenario_id=scenario.scenario_id,
        scenario_name=scenario.name,
        seed_used=seed_used,
        defenses_configured=req.defenses,
        interventions_triggered=defended_run.defense_interventions,
        baseline_run_id=baseline_run.run_id,
        baseline_peak_temp=baseline_run.peak_temperature,
        baseline_peak_current=baseline_run.peak_current,
        baseline_fault_triggered=baseline_run.fault_triggered,
        defended_run_id=defended_run.run_id,
        defended_peak_temp=defended_run.peak_temperature,
        defended_peak_current=defended_run.peak_current,
        defended_fault_triggered=defended_run.fault_triggered,
        temp_reduction_deg_c=temp_reduct,
        current_reduction_a=curr_reduct,
        percent_temp_improvement=pct_imp,
        is_defense_effective=is_effective,
        summary=summary,
        limitations="Simulation model results only; illustrative defensive research testbed."
    )


# =========================================================================
# INVESTIGATOR GUIDANCE & BENCHMARK SCORECARD (F41, F44-F46)
# =========================================================================

@router.get("/runs/{run_id}/guidance", response_model=InvestigatorGuidance, summary="Get Investigator Checklist (F41)")
def get_run_guidance(run_id: str, db: Session = Depends(get_db)):
    """Synthesizes evidence, links, and physics residuals into a structured investigative checklist."""
    run = Repository.get_run(db, run_id)
    if not run:
        raise HTTPException(status_code=404, detail=f"Run '{run_id}' not found.")
    links = Repository.get_correlation_links(db, run_id)
    if not links:
        links = CorrelationEngine.analyze_run(run)
    residual_stats = PhysicsConsistencyChecker.evaluate_telemetry(run.telemetry)
    return InvestigatorGuidanceEngine.generate_guidance(run_id, links, run.telemetry, residual_stats)


@router.get("/evaluation/benchmark", response_model=EvaluationScorecardResponse, summary="Run Evaluation Benchmark (F44, F45, F46)")
def run_evaluation_benchmark(
    split: str = Query("tuning", description="Split name: 'tuning' or 'held_out'"),
    seed: int = Query(42, description="Reproducibility random seed")
):
    """
    Computes precision, recall, false-link rate, classification accuracy,
    and compares against the 60s spike baseline with strict physical vs software latency distinction.
    """
    try:
        return EvaluationEngine.evaluate_split(split_name=split, seed=seed)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Benchmark evaluation failed: {str(e)}")


@router.get("/graph", summary="Component Dependency Graph Definition (F20)")
def get_graph():
    """Returns directed dependency graph nodes and edges for component visualization."""
    return dependency_graph.get_graph_export()


# =========================================================================
# TIER 3: FLEET & GRID FEEDER DIGITAL TWIN (F09, F10, F37)
# =========================================================================

@router.get("/fleet/scenarios", response_model=List[FleetScenario], summary="List Predefined Fleet Scenarios (F10)")
def list_fleet_scenarios():
    """Returns standard predefined fleet scenarios (10 to 50 simulated EV chargers on a shared feeder)."""
    return FleetSimulationEngine.get_predefined_fleet_scenarios()


@router.post("/fleet/run", response_model=FleetSimulationRun, summary="Execute Fleet Simulation Run (F09, F10, F37)")
def run_fleet_simulation(scenario: FleetScenario, seed: Optional[int] = Query(None), db: Session = Depends(get_db)):
    """
    Executes a deterministic multi-charger fleet simulation coupled to a shared distribution grid feeder.
    Tracks individual charger states, aggregate active power (kW), and feeder voltage sag.
    """
    try:
        run_result = FleetSimulationEngine.run_fleet(scenario, seed=seed)
        Repository.save_fleet_run(db, run_result)
        return run_result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fleet simulation failed: {str(e)}")


# =========================================================================
# TIER 3: EVENT TAXONOMY & MITRE ATT&CK FOR ICS (F14)
# =========================================================================

@router.get("/taxonomy", summary="List Event Taxonomy & MITRE ATT&CK Mappings (F14)")
def get_taxonomy():
    """Returns complete event taxonomy with authoritative MITRE ATT&CK for ICS mappings and coverage stats."""
    return {
        "summary": EventTaxonomyCatalog.get_summary_statistics(),
        "mappings": [m.model_dump() for m in EventTaxonomyCatalog.list_all_mappings()]
    }


@router.get("/taxonomy/{event_type}", summary="Get Event Type Taxonomy Mapping (F14)")
def get_event_taxonomy(event_type: str):
    """Retrieves MITRE ATT&CK for ICS mapping for a specific event type."""
    mapping = EventTaxonomyCatalog.get_mapping(event_type)
    if not mapping:
        raise HTTPException(status_code=404, detail=f"Event type '{event_type}' not found in taxonomy catalog.")
    return mapping.model_dump()


# =========================================================================
# TIER 3: MASKED-ATTACK DETECTION & ANOMALY ASSISTANT (F25, F28)
# =========================================================================

@router.get("/runs/{run_id}/masked-attacks", summary="Detect Masked Cyber Attacks (F25)")
def detect_masked_attacks(run_id: str, db: Session = Depends(get_db)):
    """
    Scans run telemetry for discrepancies where physical model variables diverge
    from sensor-reported states (e.g. frozen thermistor during high Joule heating).
    """
    run = Repository.get_run(db, run_id)
    if not run:
        raise HTTPException(status_code=404, detail=f"Run '{run_id}' not found.")
    
    # Check if counterfactual exists
    cf = Repository.get_counterfactual_for_run(db, run_id)
    cf_dict = cf.model_dump() if cf else None

    findings = MaskedAttackDetector.analyze(run.telemetry, run.events, counterfactual_difference=cf_dict)
    return {
        "run_id": run_id,
        "scenario_id": run.scenario_id,
        "masked_attack_detected": len(findings) > 0,
        "findings_count": len(findings),
        "findings": [f.model_dump() for f in findings]
    }


@router.get("/runs/{run_id}/anomaly-assistant", summary="Isolation Forest Anomaly Assistant (F28)")
def evaluate_anomaly_assistant(run_id: str, db: Session = Depends(get_db)):
    """
    Evaluates multivariate statistical anomalies using scikit-learn Isolation Forest.
    Returns normalized anomaly score and interpretable feature contribution comparisons.
    """
    run = Repository.get_run(db, run_id)
    if not run:
        raise HTTPException(status_code=404, detail=f"Run '{run_id}' not found.")
    
    result = AnomalyDetectionAssistant.evaluate(run.telemetry)
    return result.model_dump()


# =========================================================================
# TIER 3: INCIDENT COMPARISON (F38)
# =========================================================================

@router.post("/runs/compare", summary="Compare Two Simulation Runs Side-by-Side (F38)")
def compare_runs(payload: Dict[str, str], db: Session = Depends(get_db)):
    """Compares two stored incident runs side-by-side with numerical safety deltas and compatibility checks."""
    run_id_a = payload.get("run_a_id")
    run_id_b = payload.get("run_b_id")

    if not run_id_a or not run_id_b:
        raise HTTPException(status_code=400, detail="Both 'run_a_id' and 'run_b_id' are required in JSON payload.")

    run_a = Repository.get_run(db, run_id_a)
    run_b = Repository.get_run(db, run_id_b)

    if not run_a:
        raise HTTPException(status_code=404, detail=f"Run '{run_id_a}' not found.")
    if not run_b:
        raise HTTPException(status_code=404, detail=f"Run '{run_id_b}' not found.")

    return IncidentComparator.compare(run_a.model_dump(), run_b.model_dump())


# =========================================================================
# TIER 3: REPORTS & EVIDENCE-GROUNDED NARRATIVES (F42, F43)
# =========================================================================

@router.get("/runs/{run_id}/narrative", summary="Generate Evidence-Grounded Narrative (F43)")
def get_run_narrative(run_id: str, db: Session = Depends(get_db)):
    """Generates a deterministic narrative strictly referencing verified evidence tokens."""
    run = Repository.get_run(db, run_id)
    if not run:
        raise HTTPException(status_code=404, detail=f"Run '{run_id}' not found.")
    
    links = Repository.get_correlation_links(db, run_id)
    if not links:
        links = CorrelationEngine.analyze_run(run)
    links_dicts = [l.model_dump() if hasattr(l, "model_dump") else l for l in links]

    cf = Repository.get_counterfactual_for_run(db, run_id)
    cf_dict = cf.model_dump() if cf else None

    masked = MaskedAttackDetector.analyze(run.telemetry, run.events, cf_dict)
    masked_dicts = [m.model_dump() for m in masked]

    narrative = NarrativeGenerator.generate(
        run.model_dump(),
        links_dicts,
        counterfactual_result=cf_dict,
        masked_findings=masked_dicts
    )
    return narrative.model_dump()


@router.get("/runs/{run_id}/report/markdown", summary="Export Markdown Incident Report (F42)")
def export_markdown_report(run_id: str, db: Session = Depends(get_db)):
    """Exports comprehensive incident report as formatted Markdown text."""
    run = Repository.get_run(db, run_id)
    if not run:
        raise HTTPException(status_code=404, detail=f"Run '{run_id}' not found.")
    
    links = Repository.get_correlation_links(db, run_id) or CorrelationEngine.analyze_run(run)
    links_dicts = [l.model_dump() if hasattr(l, "model_dump") else l for l in links]
    cf = Repository.get_counterfactual_for_run(db, run_id)
    cf_dict = cf.model_dump() if cf else None
    masked = MaskedAttackDetector.analyze(run.telemetry, run.events, cf_dict)
    masked_dicts = [m.model_dump() for m in masked]

    narrative = NarrativeGenerator.generate(run.model_dump(), links_dicts, counterfactual_result=cf_dict, masked_findings=masked_dicts)
    md_content = ReportGenerator.generate_markdown(run.model_dump(), narrative, links_dicts, cf_dict)
    
    return Response(
        content=md_content,
        media_type="text/markdown",
        headers={"Content-Disposition": f'attachment; filename="ThreatLens_Report_{run_id}.md"'}
    )


@router.get("/runs/{run_id}/report/pdf", summary="Export PDF Incident Report (F42)")
def export_pdf_report(run_id: str, db: Session = Depends(get_db)):
    """Exports professional PDF incident report generated locally via ReportLab."""
    run = Repository.get_run(db, run_id)
    if not run:
        raise HTTPException(status_code=404, detail=f"Run '{run_id}' not found.")
    
    links = Repository.get_correlation_links(db, run_id) or CorrelationEngine.analyze_run(run)
    links_dicts = [l.model_dump() if hasattr(l, "model_dump") else l for l in links]
    cf = Repository.get_counterfactual_for_run(db, run_id)
    cf_dict = cf.model_dump() if cf else None
    masked = MaskedAttackDetector.analyze(run.telemetry, run.events, cf_dict)
    masked_dicts = [m.model_dump() for m in masked]

    narrative = NarrativeGenerator.generate(run.model_dump(), links_dicts, counterfactual_result=cf_dict, masked_findings=masked_dicts)
    pdf_bytes = ReportGenerator.generate_pdf(run.model_dump(), narrative, links_dicts, cf_dict)

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="ThreatLens_Report_{run_id}.pdf"'}
    )


# =========================================================================
# TIER 3: ABLATION ANALYSIS & PUBLIC DATASET ADAPTER (F18, F47)
# =========================================================================

@router.get("/evaluation/ablation", summary="Run Ablation Analysis Suite (F47)")
def get_ablation_analysis():
    """Runs systematic ablation experiments comparing full vs disabled pipeline components."""
    try:
        suite_result = AblationEngine.run_suite()
        return suite_result.model_dump()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ablation evaluation failed: {str(e)}")


@router.get("/dataset/provenance", summary="Get Public Dataset Provenance Metadata (F18)")
def get_dataset_provenance():
    """Returns provenance, source URL, licensing, and limitations for compatible public reference datasets."""
    return PublicDatasetAdapter.get_provenance_info().model_dump()


@router.get("/dataset/demo", summary="Evaluate Offline Synthetic Public Dataset Demo (F18)")
def evaluate_synthetic_dataset_demo():
    """Executes offline demonstration of public dataset ingestion adapter using synthetic benchmark profile."""
    records = PublicDatasetAdapter.generate_synthetic_demo_profile()
    return PublicDatasetAdapter.process_records(records)


@router.post("/dataset/import", summary="Import and Map Custom Dataset Records (F18)")
def import_custom_dataset(records: List[Dict[str, Any]]):
    """Maps custom tabular dataset records to ThreatLens canonical telemetry schema."""
    return PublicDatasetAdapter.process_records(records)


# =========================================================================
# THREATLENS OCPP SECURITY GATEWAY API
# =========================================================================
from backend.app.api.gateway_routes import router as gateway_router
router.include_router(gateway_router, prefix="/gateway", tags=["OCPP Gateway"])

