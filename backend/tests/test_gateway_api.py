"""
ThreatLens Gateway REST API Tests (Phase 3).

Tests the FastAPI endpoints for:
- GET /api/gateway/status
- POST /api/gateway/start and POST /api/gateway/stop
- POST /api/gateway/config
- GET /api/gateway/scenarios
- POST /api/gateway/test-scenario
- GET /api/gateway/interventions and DELETE /api/gateway/interventions
"""

import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.services.gateway_audit import gateway_audit_service
from backend.app.services.gateway_manager import gateway_manager

client = TestClient(app)


def test_gateway_status_endpoint():
    """Verify GET /api/gateway/status returns valid schema and simulation disclaimer."""
    res = client.get("/api/gateway/status")
    assert res.status_code == 200
    data = res.json()
    assert "state" in data
    assert "metrics" in data
    assert "policy" in data
    assert "audit" in data
    assert "disclaimer" in data
    assert "simulation" in data["disclaimer"].lower()


def test_gateway_scenarios_catalog_endpoint():
    """Verify GET /api/gateway/scenarios returns the 5 defined scenarios."""
    res = client.get("/api/gateway/scenarios")
    assert res.status_code == 200
    scenarios = res.json()
    assert len(scenarios) == 5
    ids = [s["id"] for s in scenarios]
    assert "benign_charging" in ids
    assert "excessive_current" in ids
    assert "command_flooding" in ids
    assert "unauthorized_command" in ids
    assert "malformed_message" in ids


def test_gateway_config_update_endpoint():
    """Verify POST /api/gateway/config dynamically updates policy parameters."""
    res = client.post(
        "/api/gateway/config",
        json={"current_cap_value": 115.0, "min_command_interval_seconds": 4.5},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["policy"]["current_cap_value"] == 115.0
    assert data["policy"]["min_command_interval_seconds"] == 4.5

    # Reset back to default
    client.post(
        "/api/gateway/config",
        json={"current_cap_value": 100.0, "min_command_interval_seconds": 5.0},
    )


def test_gateway_interventions_endpoints():
    """Verify GET and DELETE /api/gateway/interventions."""
    # Seed a dummy event
    gateway_audit_service.record_event({
        "timestamp": 1234567.89,
        "charge_point_id": "CP_TEST",
        "unique_id": "dummy-01",
        "action": "SetChargingProfile",
        "direction": "CSMS_TO_CHARGER",
        "decision": "CLAMP",
        "rule_id": "R-01",
        "reason": "Exceeded safe cap",
        "original_limit": 180.0,
        "modified_limit": 100.0,
    })

    # Fetch
    res = client.get("/api/gateway/interventions")
    assert res.status_code == 200
    data = res.json()
    assert data["total_records"] >= 1
    assert data["interventions"][0]["decision"] == "CLAMP"

    # Filter by decision
    res_filtered = client.get("/api/gateway/interventions?decision=CLAMP")
    assert res_filtered.status_code == 200
    assert len(res_filtered.json()["interventions"]) >= 1

    # Clear
    res_clear = client.delete("/api/gateway/interventions")
    assert res_clear.status_code == 200
    assert res_clear.json()["total_records"] == 0


def test_gateway_run_scenario_while_already_running():
    """
    Verify POST /api/gateway/test-scenario when Gateway is already started and RUNNING.
    Reuses existing MockCSMS without Errno 10048 port collision.
    Uses dedicated test ports (9500/9501) on a persistent event loop.
    """
    import asyncio
    import httpx

    async def _test():
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as ac:
            # 1. Start Gateway first (as user did in UI)
            res_start = await ac.post("/api/gateway/start", json={"charger_port": 9500, "csms_port": 9501})
            assert res_start.status_code == 200
            assert res_start.json()["is_running"] is True

            try:
                # 2. Run scenario while gateway is already running
                res_scen = await ac.post(
                    "/api/gateway/test-scenario",
                    json={"scenario_id": "excessive_current", "charger_id": "CP_LIVE_REUSE"},
                )
                assert res_scen.status_code == 200
                data = res_scen.json()
                assert data["status"] == "SUCCESS"
                assert data["verification_passed"] is True
                assert data["charger_received_limit"] == 100.0
            finally:
                # 3. Cleanly stop gateway
                res_stop = await ac.post("/api/gateway/stop")
                assert res_stop.status_code == 200
                assert res_stop.json()["is_running"] is False

    asyncio.run(_test())


