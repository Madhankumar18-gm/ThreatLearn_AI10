"""
ThreatLens Gateway Lifecycle Manager Service.

Controls asynchronous startup, shutdown, and live policy configuration for
the ThreatLens OCPP 1.6-J Gateway service inside the FastAPI process.
"""

import asyncio
import contextlib
import logging
import time
from typing import Any, Dict, Optional

from gateway.config import GatewayConfig
from gateway.mock.mock_csms import MockCSMS
from gateway.policy import GatewayPolicyEngine, PolicyConfig
from gateway.proxy import GatewayProxy
from gateway.scenarios import SCENARIO_CATALOG, ScenarioExecutionResult, ScenarioRunner
from backend.app.services.gateway_audit import gateway_audit_service

logger = logging.getLogger("ThreatLens.Gateway.Manager")


class GatewayManager:
    """Manages the Gateway background service, mock testbench, and configuration."""

    def __init__(self):
        self.config = GatewayConfig()
        self.proxy: Optional[GatewayProxy] = None
        self.mock_csms: Optional[MockCSMS] = None
        self.state: str = "STOPPED"  # "STOPPED", "STARTING", "RUNNING", "ERROR"
        self.start_time: Optional[float] = None
        self._lock = asyncio.Lock()
        self.last_error: Optional[str] = None

    @property
    def is_running(self) -> bool:
        return self.state == "RUNNING" and self.proxy is not None and self.proxy.is_running

    async def start_gateway(
        self,
        charger_port: int = 9000,
        csms_port: int = 9001,
        start_mock_csms: bool = True,
    ) -> Dict[str, Any]:
        """Start the Gateway service and upstream Mock CSMS on localhost."""
        async with self._lock:
            if self.is_running:
                return self.get_status()

            self.state = "STARTING"
            self.last_error = None
            self.config.charger_port = charger_port
            self.config.csms_port = csms_port

            try:
                # 1. Start upstream Mock CSMS if requested
                if start_mock_csms:
                    if self.mock_csms:
                        await self.mock_csms.stop()
                    self.mock_csms = MockCSMS(host=self.config.csms_host, port=self.config.csms_port)
                    await self.mock_csms.start()

                # 2. Start GatewayProxy
                self.proxy = GatewayProxy(
                    config=self.config,
                    audit_callback=gateway_audit_service.record_event,
                )
                await self.proxy.start()

                self.state = "RUNNING"
                self.start_time = time.time()
                logger.info(
                    "Gateway service started: ws://%s:%d -> ws://%s:%d",
                    self.config.host,
                    self.config.charger_port,
                    self.config.csms_host,
                    self.config.csms_port,
                )
                return self.get_status()

            except Exception as exc:
                self.state = "ERROR"
                self.last_error = str(exc)
                logger.exception("Failed to start Gateway service: %s", exc)
                # Clean up if partially started
                if self.proxy:
                    with contextlib.suppress(Exception):
                        await self.proxy.stop()
                    self.proxy = None
                if self.mock_csms:
                    with contextlib.suppress(Exception):
                        await self.mock_csms.stop()
                    self.mock_csms = None
                raise

    async def stop_gateway(self) -> Dict[str, Any]:
        """Stop the Gateway service and mock CSMS."""
        async with self._lock:
            if self.proxy:
                with contextlib.suppress(Exception):
                    await self.proxy.stop()
                self.proxy = None

            if self.mock_csms:
                with contextlib.suppress(Exception):
                    await self.mock_csms.stop()
                self.mock_csms = None

            self.state = "STOPPED"
            self.start_time = None
            logger.info("Gateway service stopped.")
            return self.get_status()

    def update_policy_config(self, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update live policy thresholds on the running engine."""
        self.config.policy.current_cap_enabled = updates.get("current_cap_enabled", self.config.policy.current_cap_enabled)
        if "current_cap_value" in updates and updates["current_cap_value"] is not None:
            self.config.policy.current_cap_value = float(updates["current_cap_value"])
        self.config.policy.rate_limiting_enabled = updates.get("rate_limiting_enabled", self.config.policy.rate_limiting_enabled)
        if "min_command_interval_seconds" in updates and updates["min_command_interval_seconds"] is not None:
            self.config.policy.min_command_interval_seconds = float(updates["min_command_interval_seconds"])
        self.config.policy.auth_validation_enabled = updates.get("auth_validation_enabled", self.config.policy.auth_validation_enabled)
        self.config.policy.thermal_lockout_enabled = updates.get("thermal_lockout_enabled", self.config.policy.thermal_lockout_enabled)
        if "thermal_lockout_threshold_c" in updates and updates["thermal_lockout_threshold_c"] is not None:
            self.config.policy.thermal_lockout_threshold_c = float(updates["thermal_lockout_threshold_c"])

        if self.proxy:
            self.proxy.policy_engine.update_config(
                current_cap_enabled=self.config.policy.current_cap_enabled,
                current_cap_value=self.config.policy.current_cap_value,
                rate_limiting_enabled=self.config.policy.rate_limiting_enabled,
                min_command_interval_seconds=self.config.policy.min_command_interval_seconds,
                auth_validation_enabled=self.config.policy.auth_validation_enabled,
                thermal_lockout_enabled=self.config.policy.thermal_lockout_enabled,
                thermal_lockout_threshold_c=self.config.policy.thermal_lockout_threshold_c,
            )
        return self.get_status()

    async def run_scenario(self, scenario_id: str, charger_id: str = "CP_DEMO_01") -> ScenarioExecutionResult:
        """Execute a reproducible test scenario."""
        if scenario_id not in SCENARIO_CATALOG:
            raise ValueError(f"Unknown scenario '{scenario_id}'")

        # Automatically start gateway if not running
        if not self.is_running:
            await self.start_gateway(
                charger_port=self.config.charger_port,
                csms_port=self.config.csms_port,
                start_mock_csms=True,
            )

        runner = ScenarioRunner(proxy=self.proxy, csms=self.mock_csms)
        result = await runner.run(scenario_id=scenario_id, charger_id=charger_id, config=self.config)
        return result

    def get_status(self) -> Dict[str, Any]:
        """Return comprehensive gateway status and metrics."""
        uptime = (time.time() - self.start_time) if (self.is_running and self.start_time) else 0.0
        active_sessions = len(self.proxy.active_sessions) if (self.proxy and self.proxy.active_sessions) else 0

        metrics = {
            "total_messages": self.proxy.total_messages if self.proxy else 0,
            "allowed": self.proxy.total_allowed if self.proxy else 0,
            "clamped": self.proxy.total_clamped if self.proxy else 0,
            "blocked": self.proxy.total_blocked if self.proxy else 0,
            "errors": self.proxy.total_errors if self.proxy else 0,
        }

        policy_dict = {
            "current_cap_enabled": self.config.policy.current_cap_enabled,
            "current_cap_value": self.config.policy.current_cap_value,
            "hardware_max_current": self.config.policy.hardware_max_current,
            "rate_limiting_enabled": self.config.policy.rate_limiting_enabled,
            "min_command_interval_seconds": self.config.policy.min_command_interval_seconds,
            "auth_validation_enabled": self.config.policy.auth_validation_enabled,
            "thermal_lockout_enabled": self.config.policy.thermal_lockout_enabled,
            "thermal_lockout_threshold_c": self.config.policy.thermal_lockout_threshold_c,
        }

        return {
            "state": self.state,
            "is_running": self.is_running,
            "host": self.config.host,
            "charger_port": self.config.charger_port,
            "csms_port": self.config.csms_port,
            "uptime_seconds": round(uptime, 2),
            "active_sessions": active_sessions,
            "metrics": metrics,
            "policy": policy_dict,
            "audit": gateway_audit_service.get_metrics(),
            "disclaimer": (
                "ThreatLens OCPP Security Gateway is a research prototype and cyber-physical "
                "software simulation; it does not certify physical electrical breaker safety or hardware contactor compliance."
            ),
        }


# Global singleton manager
gateway_manager = GatewayManager()
