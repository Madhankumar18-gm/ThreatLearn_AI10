"""
ThreatLens Repeatable Gateway Scenarios Integration Test Suite (Phase 2).

Tests the 5 end-to-end reproducible test scenarios through MockCSMS <-> GatewayProxy <-> MockChargePoint:
1. benign_charging (100% ALLOW)
2. excessive_current (CLAMP to 100A)
3. command_flooding (Rule R-02 BLOCK)
4. unauthorized_command (Rule R-03 BLOCK)
5. malformed_message (FormationViolation BLOCK)
"""

import asyncio
import pytest

from gateway.config import GatewayConfig
from gateway.scenarios import SCENARIO_CATALOG, ScenarioRunner


def test_scenario_catalog_metadata():
    """Verify that all 5 scenarios are documented in the catalog with required metadata."""
    assert len(SCENARIO_CATALOG) == 5
    expected_ids = {"benign_charging", "excessive_current", "command_flooding", "unauthorized_command", "malformed_message"}
    assert set(SCENARIO_CATALOG.keys()) == expected_ids
    for sid, info in SCENARIO_CATALOG.items():
        assert info.name
        assert info.description
        assert info.mitigation_rule


def test_scenario_benign_charging():
    """Verify benign charging scenario runs end-to-end with 100% ALLOW."""
    async def _run():
        config = GatewayConfig(charger_port=9400, csms_port=9401)
        runner = ScenarioRunner()
        result = await runner.run("benign_charging", charger_id="CP_TEST_BENIGN", config=config)

        assert result.status == "SUCCESS"
        assert result.verification_passed is True
        assert result.charger_received_limit == 90.0
        # All recorded decisions must be ALLOW
        for d in result.decisions:
            assert d["decision"] == "ALLOW"

    asyncio.run(_run())


def test_scenario_excessive_current():
    """Verify overcurrent manipulation (180A) is clamped to safe cap 100A."""
    async def _run():
        config = GatewayConfig(charger_port=9410, csms_port=9411)
        config.policy.current_cap_enabled = True
        config.policy.current_cap_value = 100.0

        runner = ScenarioRunner()
        result = await runner.run("excessive_current", charger_id="CP_TEST_OVERCURRENT", config=config)

        assert result.status == "SUCCESS"
        assert result.verification_passed is True
        assert result.charger_received_limit == 100.0

        clamp_events = [d for d in result.decisions if d["decision"] == "CLAMP"]
        assert len(clamp_events) >= 1
        assert clamp_events[0]["rule_id"] == "R-01"
        assert clamp_events[0]["original_limit"] == 180.0
        assert clamp_events[0]["modified_limit"] == 100.0

    asyncio.run(_run())


def test_scenario_command_flooding():
    """Verify command flutter / rapid setpoints trigger Rule R-02 rate limiting."""
    async def _run():
        config = GatewayConfig(charger_port=9420, csms_port=9421)
        config.policy.rate_limiting_enabled = True
        config.policy.min_command_interval_seconds = 5.0

        runner = ScenarioRunner()
        result = await runner.run("command_flooding", charger_id="CP_TEST_FLOOD", config=config)

        assert result.status == "SUCCESS"
        assert result.verification_passed is True

        block_events = [d for d in result.decisions if d["decision"] == "BLOCK"]
        assert len(block_events) >= 2
        for b in block_events:
            assert b["rule_id"] == "R-02"

    asyncio.run(_run())


def test_scenario_unauthorized_command():
    """Verify unauthorized start injection triggers Rule R-03 SecurityError."""
    async def _run():
        config = GatewayConfig(charger_port=9430, csms_port=9431)
        config.policy.auth_validation_enabled = True

        runner = ScenarioRunner()
        result = await runner.run("unauthorized_command", charger_id="CP_TEST_UNAUTH", config=config)

        assert result.status == "SUCCESS"
        assert result.verification_passed is True

        block_events = [d for d in result.decisions if d["decision"] == "BLOCK"]
        assert len(block_events) == 1
        assert block_events[0]["rule_id"] == "R-03"
        assert block_events[0]["error_code"] == "SecurityError"

    asyncio.run(_run())


def test_scenario_malformed_message():
    """Verify syntactic frame violation returns FormationViolation."""
    async def _run():
        config = GatewayConfig(charger_port=9440, csms_port=9441)
        runner = ScenarioRunner()
        result = await runner.run("malformed_message", charger_id="CP_TEST_MALF", config=config)

        assert result.status == "SUCCESS"
        assert result.verification_passed is True

    asyncio.run(_run())
