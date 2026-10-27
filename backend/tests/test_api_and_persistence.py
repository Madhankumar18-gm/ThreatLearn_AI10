"""
Tests for API Endpoints and SQLite Persistence (Features F50, F51, Acceptance Criteria 13 & 14).
"""

import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.database.session import SessionLocal, init_db
from backend.app.database.repository import Repository


@pytest.fixture(scope="module")
def client():
    init_db()
    with TestClient(app) as test_client:
        yield test_client


def test_health_endpoint(client):
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert data["simulation_mode"] is True
    assert data["total_scenarios"] >= 25


def test_scenarios_endpoints(client):
    res = client.get("/api/scenarios")
    assert res.status_code == 200
    scenarios = res.json()
    assert len(scenarios) >= 25

    # Filter by family
    res_filtered = client.get("/api/scenarios?family=Attack")
    assert res_filtered.status_code == 200
    atk_scenarios = res_filtered.json()
    assert len(atk_scenarios) >= 4
    for s in atk_scenarios:
        assert s["family"] == "Attack"

    # Single scenario
    res_single = client.get("/api/scenarios/SCN-NORM-01")
    assert res_single.status_code == 200
    assert res_single.json()["scenario_id"] == "SCN-NORM-01"


def test_api_input_validation_and_error_responses(client):
    """Criteria 13: API endpoints validate inputs and return useful error responses."""
    # 404 for unknown scenario ID
    res = client.get("/api/scenarios/UNKNOWN-SCN-999")
    assert res.status_code == 404

    # 404 for run on non-existent scenario
    res = client.post("/api/runs", json={"scenario_id": "NON-EXISTENT-ID"})
    assert res.status_code == 404

    # 400 for negative/invalid seed
    res = client.post("/api/runs", json={"scenario_id": "SCN-NORM-01", "seed": -5})
    assert res.status_code == 400
    assert "Seed must be a non-negative" in res.json()["detail"]


def test_run_simulation_and_persistence_across_sessions(client):
    """Criteria 14: Incident history survives backend restarts."""
    # Step 1: Run a simulation via API
    post_res = client.post("/api/runs", json={"scenario_id": "SCN-ATK-01", "seed": 777})
    assert post_res.status_code == 200
    run_data = post_res.json()
    run_id = run_data["run_id"]
    assert run_id.startswith("RUN-")
    assert run_data["peak_current"] > 0

    # Step 2: Retrieve incident history list
    list_res = client.get("/api/runs")
    assert list_res.status_code == 200
    history = list_res.json()
    run_ids = [r["run_id"] for r in history]
    assert run_id in run_ids

    # Step 3: Fetch full run details
    detail_res = client.get(f"/api/runs/{run_id}")
    assert detail_res.status_code == 200
    fetched_run = detail_res.json()
    assert fetched_run["run_id"] == run_id
    assert len(fetched_run["telemetry"]) > 0

    # Step 4: Fetch correlated links
    links_res = client.get(f"/api/runs/{run_id}/links")
    assert links_res.status_code == 200
    links = links_res.json()
    assert len(links) > 0

    # Step 5: Test Counterfactual replay via API
    cf_res = client.post(
        f"/api/runs/{run_id}/counterfactual",
        json={"target_event_id": "EVT-ATK-01-B"}
    )
    assert cf_res.status_code == 200
    cf_data = cf_res.json()
    assert cf_data["effect_attribution"] in ("DISAPPEARED", "DECREASED")
    assert len(cf_data["overlay_data"]) > 0

    # Step 6: Verify direct SQLite database persistence (simulating complete app restart)
    db = SessionLocal()
    try:
        persisted_run = Repository.get_run(db, run_id)
        assert persisted_run is not None, "Run must persist in SQLite!"
        assert persisted_run.run_id == run_id
        assert persisted_run.peak_current == run_data["peak_current"]

        persisted_cf = Repository.get_counterfactual_for_run(db, run_id, "EVT-ATK-01-B")
        assert persisted_cf is not None, "Counterfactual result must persist in SQLite!"
        assert persisted_cf.original_run_id == run_id
    finally:
        db.close()
