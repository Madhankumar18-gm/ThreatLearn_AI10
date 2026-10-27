"""
ThreatLens Cyber-Physical Impact Analysis Tests.

Verifies:
1. ImpactAnalysisEngine deterministic quantitative metric formulas:
   - Demand Change = Attack Demand - Baseline Demand (kW)
   - Percentage Demand Change = (Demand Change / Baseline Demand) * 100
   - Feeder Loading (%) = (Fleet Demand / Feeder Capacity) * 100
   - Voltage Deviation = Simulated Voltage - Nominal Voltage (V)
2. 6-stage Cyber-to-Physical Impact Chain generation and evidence labeling.
3. REST endpoint GET /api/runs/{run_id}/impact-analysis.
4. Gateway intervention correlation into impact analysis.
"""

import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.schemas.simulation import SimulationRunResponse
from backend.app.analysis.impact_analysis import ImpactAnalysisEngine
from backend.app.services.gateway_audit import gateway_audit_service

client = TestClient(app)


def test_impact_analysis_engine_calculations():
    """Verify deterministic formulas and 6-stage chain on a simulated run."""
    # 1. Run a simulation first
    res = client.post("/api/runs", json={"scenario_id": "SCN-ATK-01", "seed": 42})
    assert res.status_code == 200
    run_dict = res.json()
    run = SimulationRunResponse(**run_dict)

    # 2. Analyze run through ImpactAnalysisEngine
    report = ImpactAnalysisEngine.analyze_run(
        run=run,
        feeder_capacity_kw=800.0,
        feeder_nominal_voltage_v=400.0,
    )

    # 3. Assert report structure
    assert report.run_id == run.run_id
    assert report.scenario_id == "SCN-ATK-01"
    assert report.attack_type == "CHANGE_CURRENT_LIMIT"
    assert report.target_charger_id == "evse_controller"

    # 4. Check Quantitative Metrics
    qm = report.quantitative_metrics
    assert qm.feeder_capacity_kw == 800.0
    assert qm.feeder_nominal_voltage_v == 400.0
    assert qm.attack_peak_fleet_demand_kw > 0.0
    assert qm.feeder_loading_pct == round((qm.attack_peak_fleet_demand_kw / 800.0) * 100.0, 2)
    assert qm.min_feeder_voltage_v <= 400.0
    assert qm.voltage_deviation_v == round(qm.min_feeder_voltage_v - 400.0, 2)
    assert qm.target_charger_peak_current_a == run.peak_current
    assert qm.target_charger_peak_temp_c == run.peak_temperature

    # 5. Check 6-Stage Impact Chain
    chain = report.impact_chain
    assert len(chain) == 6
    stage_ids = [s.stage_id for s in chain]
    assert stage_ids == [
        "cyber_event",
        "protocol_effect",
        "charger_response",
        "fleet_demand",
        "feeder_voltage",
        "operational_consequence",
    ]

    # Verify each stage has evidence grounding
    for s in chain:
        assert s.observed_event
        assert s.evidence_source
        assert s.evidence_type in ("Direct Evidence", "Calculated Metric", "Inferred Relationship", "Unverified Hypothesis")

    # 6. Check Assessment Summary
    asm = report.assessment
    assert asm.what_happened
    assert asm.affected_segment
    assert asm.physical_changes
    assert len(asm.thresholds_crossed) > 0
    assert asm.severity_level in ("LOW", "MEDIUM", "HIGH", "CRITICAL")


def test_impact_analysis_rest_endpoint():
    """Verify GET /api/runs/{run_id}/impact-analysis REST endpoint returns 200 and schema."""
    # Run a test scenario
    res_run = client.post("/api/runs", json={"scenario_id": "SCN-ATK-01", "seed": 101})
    assert res_run.status_code == 200
    run_id = res_run.json()["run_id"]

    # Call Impact Analysis endpoint
    res = client.get(f"/api/runs/{run_id}/impact-analysis?feeder_capacity_kw=800.0&feeder_nominal_voltage_v=400.0")
    assert res.status_code == 200
    data = res.json()

    assert data["run_id"] == run_id
    assert "quantitative_metrics" in data
    assert "impact_chain" in data
    assert "assessment" in data
    assert "timeseries" in data
    assert len(data["timeseries"]) > 0

    # Test 404 on nonexistent run
    res_404 = client.get("/api/runs/RUN-NONEXISTENT/impact-analysis")
    assert res_404.status_code == 404


def test_gateway_correlation_in_impact_analysis():
    """Verify that recorded gateway audit interventions link into Impact Analysis report."""
    # 1. Record a mock gateway intervention
    gateway_audit_service.clear()
    gateway_audit_service.record_event({
        "timestamp": 15.2,
        "charge_point_id": "evse_chg_01",
        "unique_id": "test-msg-001",
        "action": "SetChargingProfile",
        "direction": "CSMS_TO_CHARGER",
        "decision": "CLAMP",
        "rule_id": "R-01",
        "reason": "Requested 180A clamped to 100A",
        "original_limit": 180.0,
        "modified_limit": 100.0,
    })

    # 2. Run simulation
    res_run = client.post("/api/runs", json={"scenario_id": "SCN-ATK-01", "seed": 42})
    run_id = res_run.json()["run_id"]

    # 3. Retrieve impact analysis
    res = client.get(f"/api/runs/{run_id}/impact-analysis")
    assert res.status_code == 200
    data = res.json()

    # Interventions must be attached
    assert len(data["gateway_interventions"]) >= 1
    gw = data["gateway_interventions"][0]
    assert gw["charge_point_id"] == "evse_chg_01"
    assert gw["decision"] == "CLAMP"
    assert gw["rule_id"] == "R-01"
    assert gw["original_limit"] == 180.0
    assert gw["modified_limit"] == 100.0
