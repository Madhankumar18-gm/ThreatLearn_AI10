"""
ThreatLens OCPP Gateway REST API Endpoints.

Provides administrative controls, status monitoring, policy tuning,
audit intervention logs, and repeatable scenario test execution.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Any, Dict, List, Optional

from backend.app.schemas.gateway import (
    GatewayInterventionRecord,
    GatewayInterventionsResponse,
    GatewayPolicyUpdateRequest,
    GatewayScenarioCatalogItem,
    GatewayScenarioRunRequest,
    GatewayScenarioRunResponse,
    GatewayStartRequest,
    GatewayStatusResponse,
)
from backend.app.services.gateway_audit import gateway_audit_service
from backend.app.services.gateway_manager import gateway_manager
from gateway.scenarios import SCENARIO_CATALOG

router = APIRouter()


@router.get("/status", response_model=GatewayStatusResponse, summary="Get Gateway Operational Status")
def get_gateway_status():
    """Retrieve live status, WebSocket ports, session count, counters, and audit telemetry."""
    return gateway_manager.get_status()


@router.post("/start", response_model=GatewayStatusResponse, summary="Start Gateway Service")
async def start_gateway(request: Optional[GatewayStartRequest] = None):
    """Start the local loopback OCPP Gateway and upstream mock CSMS."""
    req = request or GatewayStartRequest()
    try:
        status = await gateway_manager.start_gateway(
            charger_port=req.charger_port,
            csms_port=req.csms_port,
            start_mock_csms=req.start_mock_csms,
        )
        return status
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to start Gateway: {exc}")


@router.post("/stop", response_model=GatewayStatusResponse, summary="Stop Gateway Service")
async def stop_gateway():
    """Stop the Gateway service and disconnect active WebSocket sessions."""
    try:
        status = await gateway_manager.stop_gateway()
        return status
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to stop Gateway: {exc}")


@router.post("/config", response_model=GatewayStatusResponse, summary="Update Policy Thresholds")
def update_gateway_policy(request: GatewayPolicyUpdateRequest):
    """Dynamically modify active current caps, rate limit intervals, and auth toggles."""
    updates = request.model_dump(exclude_unset=True)
    return gateway_manager.update_policy_config(updates)


@router.get("/interventions", response_model=GatewayInterventionsResponse, summary="Get Decision Interventions")
def get_gateway_interventions(
    limit: int = Query(default=100, ge=1, le=500),
    decision: Optional[str] = Query(default=None, description="Filter by ALLOW, CLAMP, or BLOCK"),
    rule: Optional[str] = Query(default=None, description="Filter by rule ID e.g. R-01"),
):
    """Fetch recorded gateway policy interventions from the non-blocking ring-buffer."""
    events = gateway_audit_service.get_events(limit=limit, decision_filter=decision, rule_filter=rule)
    return {
        "total_records": len(events),
        "interventions": events,
    }


@router.delete("/interventions", summary="Clear Intervention Logs")
def clear_gateway_interventions():
    """Clear recorded intervention events and reset audit counters."""
    gateway_audit_service.clear()
    return {"status": "cleared", "total_records": 0}


@router.get("/scenarios", response_model=List[GatewayScenarioCatalogItem], summary="Get Scenario Catalog")
def get_scenario_catalog():
    """List the five repeatable scenario definitions."""
    items = []
    for s in SCENARIO_CATALOG.values():
        items.append(
            GatewayScenarioCatalogItem(
                id=s.id,
                name=s.name,
                category=s.category,
                description=s.description,
                expected_decisions=s.expected_decisions,
                threat_actor=s.threat_actor,
                mitigation_rule=s.mitigation_rule,
            )
        )
    return items


@router.post("/test-scenario", response_model=GatewayScenarioRunResponse, summary="Execute Test Scenario")
async def run_gateway_scenario(request: GatewayScenarioRunRequest):
    """
    Execute one of the 5 repeatable test scenarios through the Gateway testbench.
    Captures live decisions and asserts pass criteria.
    """
    try:
        result = await gateway_manager.run_scenario(
            scenario_id=request.scenario_id,
            charger_id=request.charger_id or "CP_DEMO_01",
        )
        return GatewayScenarioRunResponse(
            scenario_id=result.scenario_id,
            scenario_name=result.scenario_name,
            status=result.status,
            total_messages=result.total_messages,
            decisions=result.decisions,
            charger_received_limit=result.charger_received_limit,
            summary=result.summary,
            verification_passed=result.verification_passed,
            execution_time_seconds=result.execution_time_seconds,
        )
    except ValueError as val_err:
        raise HTTPException(status_code=400, detail=str(val_err))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Scenario execution failed: {exc}")
