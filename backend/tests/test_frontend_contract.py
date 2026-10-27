"""
Frontend Contract Tests (Acceptance Criteria 15).
Verifies that all API responses match the frontend Recharts & React components contract.
"""

import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.database.session import init_db


@pytest.fixture(scope="module")
def client():
    init_db()
    with TestClient(app) as test_client:
        yield test_client


def test_frontend_scenario_and_run_contract(client):
    """Verifies that run response payload contains all keys required by frontend charts."""
    res = client.post("/api/runs", json={"scenario_id": "SCN-ATK-01", "seed": 201})
    assert res.status_code == 200
    data = res.json()

    # Required top-level keys
    for key in ["run_id", "scenario_id", "scenario_name", "scenario_family", "seed",
                "events", "telemetry", "peak_current", "peak_temperature",
                "final_soc", "fault_triggered", "threshold_crossings"]:
        assert key in data, f"Missing frontend required key '{key}' in run response"

    # Required telemetry slice keys for Recharts
    first_slice = data["telemetry"][0]
    for key in ["timestamp", "battery_temperature", "charging_current",
                "battery_voltage", "state_of_charge", "cooling_power",
                "sensor_temperature", "grid_load", "charger_state"]:
        assert key in first_slice, f"Missing telemetry field '{key}' in time slice"


def test_frontend_counterfactual_overlay_contract(client):
    """Verifies counterfactual overlay payload structure for dual-line charts."""
    run_res = client.post("/api/runs", json={"scenario_id": "SCN-ATK-01", "seed": 201})
    run_id = run_res.json()["run_id"]

    cf_res = client.post(f"/api/runs/{run_id}/counterfactual", json={"target_event_id": "EVT-ATK-01-B"})
    assert cf_res.status_code == 200
    cf_data = cf_res.json()

    for key in ["original_run_id", "counterfactual_run_id", "target_event_id",
                "peak_current_diff", "peak_temp_diff", "final_soc_diff",
                "effect_attribution", "is_causally_proven", "summary",
                "limitations", "overlay_data"]:
        assert key in cf_data, f"Missing counterfactual field '{key}'"

    first_pt = cf_data["overlay_data"][0]
    for key in ["timestamp", "original_temperature", "replay_temperature",
                "original_current", "replay_current", "original_voltage",
                "replay_voltage", "original_soc", "replay_soc"]:
        assert key in first_pt, f"Missing overlay point field '{key}'"


def test_frontend_graph_contract(client):
    """Verifies graph export structure for SVG DependencyGraphView."""
    res = client.get("/api/graph")
    assert res.status_code == 200
    graph_data = res.json()

    assert "nodes" in graph_data and "edges" in graph_data
    assert len(graph_data["nodes"]) >= 10
    assert len(graph_data["edges"]) >= 10

    first_node = graph_data["nodes"][0]
    assert "id" in first_node and "label" in first_node
