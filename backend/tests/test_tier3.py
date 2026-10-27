"""
ThreatLens Tier 3 Automated Integration & Acceptance Tests.
Verifies all Tier 3 features:
- F09: Grid feeder digital twin calculations & voltage sag
- F10: Multi-charger fleet simulation (10-50 chargers) with aggregate demand
- F14: Event taxonomy & MITRE ATT&CK for ICS mappings
- F18: Public dataset adapter & synthetic demo
- F25: Masked-attack detection with alternative explanations
- F28: Isolation Forest anomaly assistant without ground-truth leakage
- F38: Side-by-side incident comparison & delta calculation
- F42: Offline PDF (ReportLab) and Markdown report export
- F43: Evidence-grounded narrative generator
- F47: Pipeline component ablation evaluation
- REST API Tier 3 endpoints
"""

import pytest
import io
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.simulation.grid_feeder import GridFeederModel
from backend.app.schemas.fleet import FeederConfig, FleetScenario
from backend.app.simulation.fleet_simulator import FleetSimulationEngine
from backend.app.core.taxonomy import EventTaxonomyCatalog
from backend.app.analysis.masked_attack import MaskedAttackDetector
from backend.app.analysis.anomaly_detector import AnomalyDetectionAssistant
from backend.app.analysis.incident_comparison import IncidentComparator
from backend.app.analysis.narrative import NarrativeGenerator
from backend.app.reports.report_generator import ReportGenerator
from backend.app.analysis.ablation import AblationEngine
from backend.app.ingestion.public_dataset_adapter import PublicDatasetAdapter
from backend.app.scenarios.library import SCENARIOS_MAP
from backend.app.simulation.simulator import SimulationEngine

client = TestClient(app)


def test_grid_feeder_calculations():
    """Verify Grid Feeder loading ratio, voltage sag, and warning/critical thresholds (F09)."""
    cfg = FeederConfig(capacity_kw=500.0, nominal_voltage_v=400.0, warning_threshold_pct=80.0, critical_threshold_pct=95.0)
    feeder = GridFeederModel(cfg)

    # 1. 250 kW load (50% loading) -> NORMAL
    res_50 = feeder.evaluate_step(total_power_kw=250.0, total_current_a=625.0)
    assert res_50["feeder_loading_pct"] == 50.0
    assert res_50["feeder_status"] == "NORMAL"
    assert res_50["feeder_voltage_v"] < 400.0
    assert res_50["feeder_voltage_v"] > 380.0

    # 2. 420 kW load (84% loading) -> WARNING
    res_84 = feeder.evaluate_step(total_power_kw=420.0, total_current_a=1050.0)
    assert res_84["feeder_loading_pct"] == 84.0
    assert res_84["feeder_status"] == "WARNING"
    assert res_84["is_overloaded"] is True
    assert res_84["is_critical"] is False

    # 3. 490 kW load (98% loading) -> CRITICAL_OVERLOAD
    res_98 = feeder.evaluate_step(total_power_kw=490.0, total_current_a=1225.0)
    assert res_98["feeder_loading_pct"] == 98.0
    assert res_98["feeder_status"] == "CRITICAL_OVERLOAD"
    assert res_98["is_critical"] is True


def test_fleet_simulation_sizes_and_power_conservation():
    """Verify multi-charger fleet supports 10-50 chargers and aggregate power matches individual sums (F10)."""
    # Test with 20 chargers
    scn = FleetScenario(
        fleet_scenario_id="TEST-FLEET-20",
        name="Test 20 Charger Fleet",
        description="Test fleet",
        charger_count=20,
        duration_seconds=15.0,
        seed=42,
        feeder_config=FeederConfig(capacity_kw=800.0)
    )
    run_res = FleetSimulationEngine.run_fleet(scn, seed=42)

    assert run_res.charger_count == 20
    assert len(run_res.time_slices) == 16  # 0 to 15s inclusive
    first_slice = run_res.time_slices[5]
    assert len(first_slice.chargers) == 20

    # Check unique charger IDs
    charger_ids = [c.charger_id for c in first_slice.chargers]
    assert len(set(charger_ids)) == 20
    assert "CHG-01" in charger_ids
    assert "CHG-20" in charger_ids

    # Power conservation: Total power must equal sum of individual charger powers
    indiv_power_sum = sum(c.power_kw for c in first_slice.chargers)
    assert abs(first_slice.total_fleet_power_kw - indiv_power_sum) < 0.2


def test_fleet_simulation_seeded_determinism():
    """Verify fleet simulations produce bitwise-identical results under identical seed (F10)."""
    scn = FleetScenario(
        fleet_scenario_id="TEST-FLEET-DET",
        name="Determinism Test",
        description="Check determinism",
        charger_count=12,
        duration_seconds=10.0,
        seed=999
    )
    run_1 = FleetSimulationEngine.run_fleet(scn, seed=999)
    run_2 = FleetSimulationEngine.run_fleet(scn, seed=999)

    assert run_1.peak_fleet_power_kw == run_2.peak_fleet_power_kw
    assert run_1.peak_feeder_loading_pct == run_2.peak_feeder_loading_pct
    assert run_1.min_feeder_voltage_v == run_2.min_feeder_voltage_v
    assert len(run_1.time_slices) == len(run_2.time_slices)


def test_event_taxonomy_mitre_mapping():
    """Verify event taxonomy contains valid MITRE ATT&CK for ICS mappings and unmapped flags (F14)."""
    # 1. CHANGE_CURRENT_LIMIT -> T0855 (Unauthorized Command Message)
    t_cmd = EventTaxonomyCatalog.get_mapping("CHANGE_CURRENT_LIMIT")
    assert t_cmd is not None
    assert t_cmd.mitre_technique_id == "T0855"
    assert t_cmd.mitre_technique_name == "Unauthorized Command Message"
    assert t_cmd.verification_status == "VERIFIED"
    assert "https://attack.mitre.org/techniques/T0855/" in t_cmd.mitre_url

    # 2. COOLING_OVERRIDE -> T0836 (Modify Parameter)
    t_cool = EventTaxonomyCatalog.get_mapping("COOLING_OVERRIDE")
    assert t_cool is not None
    assert t_cool.mitre_technique_id == "T0836"
    assert t_cool.verification_status == "VERIFIED"

    # 3. SENSOR_DRIFT -> Unmapped Hardware Fault
    t_drift = EventTaxonomyCatalog.get_mapping("SENSOR_DRIFT")
    assert t_drift is not None
    assert t_drift.mitre_technique_id is None
    assert t_drift.verification_status == "UNMAPPED_HARDWARE_FAULT"

    # 4. START_TRANSACTION -> Unmapped Benign
    t_start = EventTaxonomyCatalog.get_mapping("START_TRANSACTION")
    assert t_start is not None
    assert t_start.mitre_technique_id is None
    assert t_start.verification_status == "UNMAPPED_BENIGN"


def test_masked_attack_detection():
    """Verify masked-attack detector identifies thermal masking while avoiding false positives on normal data (F25)."""
    # 1. Normal run should NOT trigger masked attack finding
    normal_run = SimulationEngine.run(SCENARIOS_MAP["SCN-NORM-01"], seed=101)
    normal_findings = MaskedAttackDetector.analyze(normal_run.telemetry, normal_run.events)
    assert len(normal_findings) == 0

    # 2. Masked attack run SCN-MSK-01 (overcurrent with stuck thermistor)
    masked_run = SimulationEngine.run(SCENARIOS_MAP["SCN-MSK-01"], seed=501)
    masked_findings = MaskedAttackDetector.analyze(masked_run.telemetry, masked_run.events)
    assert len(masked_findings) > 0

    finding = masked_findings[0]
    assert finding.discrepancy_magnitude >= 6.0
    assert len(finding.evidence_ids) >= 2
    assert len(finding.alternative_explanations) >= 3
    assert len(finding.recommended_verification_steps) >= 3


def test_anomaly_detection_assistant():
    """Verify Isolation Forest anomaly detector extracts features without ground-truth leakage and provides interpretable flags (F28)."""
    # Fit baseline
    normal_run = SimulationEngine.run(SCENARIOS_MAP["SCN-NORM-01"], seed=101)
    AnomalyDetectionAssistant.fit_baseline(normal_run.telemetry)

    # Evaluate normal run
    norm_result = AnomalyDetectionAssistant.evaluate(normal_run.telemetry)
    assert isinstance(norm_result.anomaly_score, float)
    assert norm_result.trained_on_nominal_only is True
    assert "ASSISTANT SIGNAL ONLY" in norm_result.assistant_disclaimer

    # Evaluate attack run (SCN-ATK-01)
    atk_run = SimulationEngine.run(SCENARIOS_MAP["SCN-ATK-01"], seed=201)
    atk_result = AnomalyDetectionAssistant.evaluate(atk_run.telemetry)
    assert atk_result.anomaly_score > norm_result.anomaly_score
    assert len(atk_result.top_contributing_features) > 0
    # Top contributor should explain deviation
    assert atk_result.top_contributing_features[0].deviation_ratio > 0.0


def test_incident_comparison():
    """Verify incident comparator calculates deltas and flags duration/seed compatibility (F38)."""
    run_a = {
        "run_id": "RUN-A",
        "scenario_id": "SCN-ATK-01",
        "duration_seconds": 60.0,
        "seed": 201,
        "peak_temperature": 58.5,
        "peak_current": 150.0,
        "peak_grid_load": 62.0,
        "safety_trip_occurred": True
    }
    # Run B is defended (lower peak temp)
    run_b = {
        "run_id": "RUN-B",
        "scenario_id": "SCN-DEF-01",
        "duration_seconds": 60.0,
        "seed": 201,
        "peak_temperature": 41.2,
        "peak_current": 100.0,
        "peak_grid_load": 40.0,
        "safety_trip_occurred": False
    }

    comp = IncidentComparator.compare(run_a, run_b)
    assert comp.is_compatible is True
    assert len(comp.metric_deltas) >= 3

    # Check temperature delta: Run B is cooler (-17.3°C)
    t_delta = next(d for d in comp.metric_deltas if "Temperature" in d.metric_name)
    assert t_delta.absolute_delta < 0.0
    assert t_delta.better_run == "RUN-B"


def test_reports_and_grounded_narrative():
    """Verify Markdown and ReportLab PDF report generation with strictly calibrated narrative evidence (F42, F43)."""
    atk_run = SimulationEngine.run(SCENARIOS_MAP["SCN-ATK-01"], seed=201)
    narrative = NarrativeGenerator.generate(
        atk_run.model_dump(),
        correlation_links=[{"event_id": "EVT-1", "event_type": "CHANGE_CURRENT_LIMIT", "source_component": "csms", "target_signal": "temperature", "confidence_score": 0.95}],
        counterfactual_result={"replay_executed": True, "delta_peak_temp": -28.5, "attribution_proven": True}
    )

    # Narrative assertions
    assert "OBSERVED:" in narrative.observations_section
    assert "INFERRED:" in narrative.inferred_causal_relationships
    assert "COUNTERFACTUAL PROOF:" in narrative.counterfactual_proof_statement
    assert len(narrative.referenced_evidence_ids) >= 2

    # Markdown export
    md_report = ReportGenerator.generate_markdown(atk_run.model_dump(), narrative)
    assert "# THREATLENS INCIDENT REPORT" in md_report
    assert "Battery Pack Temperature" in md_report

    # PDF export (ReportLab)
    pdf_bytes = ReportGenerator.generate_pdf(atk_run.model_dump(), narrative)
    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 2000
    assert pdf_bytes.startswith(b"%PDF")  # Valid PDF header


def test_ablation_analysis_suite():
    """Verify ablation suite runs 6 configurations and validates precision drop on disabled components (F47)."""
    suite = AblationEngine.run_suite()
    assert len(suite.experiments) == 6
    assert suite.scenarios_evaluated >= 4

    exp_map = {e.experiment_id: e for e in suite.experiments}
    full_prec = exp_map["EXP-FULL"].precision
    no_graph_prec = exp_map["EXP-NO-GRAPH"].precision
    no_rules_prec = exp_map["EXP-NO-RULES"].precision

    # Disabling graph and rules must noticeably degrade precision
    assert full_prec > no_graph_prec
    assert full_prec > no_rules_prec
    assert exp_map["EXP-NO-GRAPH"].false_link_rate > exp_map["EXP-FULL"].false_link_rate


def test_public_dataset_adapter():
    """Verify public dataset adapter maps columns and generates standard telemetry slices (F18)."""
    provenance = PublicDatasetAdapter.get_provenance_info()
    assert provenance.license_type == "Creative Commons Attribution 4.0 International (CC-BY-4.0)"

    records = PublicDatasetAdapter.generate_synthetic_demo_profile()
    res = PublicDatasetAdapter.process_records(records)

    assert res["success"] is True
    assert res["report"]["time_slices_generated"] == 45
    assert len(res["time_slices"]) == 45
    first_slice = res["time_slices"][0]
    assert "battery_temperature" in first_slice
    assert "charging_current" in first_slice


def test_tier3_rest_endpoints():
    """Verify all Tier 3 REST endpoints return 200 OK via FastAPI TestClient."""
    # 1. Fleet scenarios list
    r_fleet_scn = client.get("/api/fleet/scenarios")
    assert r_fleet_scn.status_code == 200
    assert len(r_fleet_scn.json()) >= 6

    # 2. Fleet simulation run
    sample_fleet = r_fleet_scn.json()[0]
    sample_fleet["duration_seconds"] = 10.0  # fast test
    r_run_fleet = client.post("/api/fleet/run", json=sample_fleet)
    assert r_run_fleet.status_code == 200
    fleet_data = r_run_fleet.json()
    assert "peak_fleet_power_kw" in fleet_data
    assert "feeder_loading_pct" in fleet_data["time_slices"][0]

    # 3. Taxonomy list
    r_tax = client.get("/api/taxonomy")
    assert r_tax.status_code == 200
    assert r_tax.json()["summary"]["mitre_verified_count"] >= 5

    # 4. Taxonomy single event
    r_tax_single = client.get("/api/taxonomy/CHANGE_CURRENT_LIMIT")
    assert r_tax_single.status_code == 200
    assert r_tax_single.json()["mitre_technique_id"] == "T0855"

    # 5. Ablation suite
    r_abl = client.get("/api/evaluation/ablation")
    assert r_abl.status_code == 200
    assert len(r_abl.json()["experiments"]) == 6

    # 6. Dataset provenance & demo
    r_prov = client.get("/api/dataset/provenance")
    assert r_prov.status_code == 200
    r_demo = client.get("/api/dataset/demo")
    assert r_demo.status_code == 200
    assert r_demo.json()["success"] is True
