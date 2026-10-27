"""
Multi-Charger Fleet Simulation Engine (Feature F10).
Simulates a configurable fleet of 10-50 EV chargers on a shared distribution feeder.
Tracks individual charger state, battery thermal dynamics, aggregate active power,
and feeder voltage sag under coordinated or targeted cyber events.
"""

import uuid
import numpy as np
from typing import List, Dict, Any, Optional

from backend.app.schemas.fleet import (
    FeederConfig, ChargerFleetSummary, FleetTimeSlice, FleetScenario, FleetSimulationRun
)
from backend.app.simulation.grid_feeder import GridFeederModel
from backend.app.simulation.state_machine import EVChargerStateMachine, ChargerState
from backend.app.simulation.battery_model import BatteryBMSModel
from backend.app.simulation.thermal_model import ThermalModel


class ChargerAgent:
    """Represents a single simulated EV charger in the fleet."""

    def __init__(
        self,
        charger_id: str,
        initial_soc: float,
        initial_temp: float,
        nominal_current_a: float,
        hardware_limit_a: float = 150.0
    ):
        self.charger_id = charger_id
        self.component_id = f"evse_{charger_id.lower()}"
        self.state_machine = EVChargerStateMachine(hardware_limit_a=hardware_limit_a)
        self.battery = BatteryBMSModel(capacity_kwh=60.0, initial_soc=initial_soc)
        self.thermal = ThermalModel(ambient_temp_c=25.0, initial_temp_c=initial_temp)
        self.nominal_current_a = nominal_current_a
        self.requested_current_a = nominal_current_a
        self.cooling_efficiency = 1.0
        self.is_affected = False
        self.active_event: Optional[str] = None
        self.cooling_override = False

        # Transition to CHARGING initially
        self.state_machine.authorize()
        self.state_machine.start_charging(nominal_current_a)

    def step(self, dt: float = 1.0, fleet_current_cap: Optional[float] = None) -> ChargerFleetSummary:
        """Advance charger state and physical models by dt seconds."""
        # Check active cooling override
        effective_cooling = 0.0 if self.cooling_override else self.cooling_efficiency
        self.thermal.cooling_factor = effective_cooling

        # Apply fleet-level mitigation cap if present
        target_current = self.requested_current_a
        if fleet_current_cap is not None:
            target_current = min(target_current, fleet_current_cap)

        # Get actual delivered current from state machine
        self.state_machine.set_requested_current(target_current)
        actual_current, _ = self.state_machine.compute_actual_current()

        # Step battery model
        voltage, soc, _ = self.battery.step(actual_current, dt)

        # Step thermal model
        temp, reported_temp, _ = self.thermal.step(
            current_a=actual_current,
            resistance_ohm=self.battery.internal_resistance_ohm,
            dt_seconds=dt,
            rng_noise=0.0
        )

        # Check BMS thermal trip (Safety limit at 60°C)
        if temp >= 60.0:
            self.state_machine.trigger_fault(f"Thermal trip: {temp:.1f}°C >= 60.0°C")
            actual_current = 0.0

        # Compute power in kW (P = V * I / 1000)
        power_kw = round((voltage * actual_current) / 1000.0, 2)

        return ChargerFleetSummary(
            charger_id=self.charger_id,
            component_id=self.component_id,
            state=self.state_machine.state.value,
            current_a=round(actual_current, 2),
            voltage_v=round(voltage, 2),
            power_kw=power_kw,
            battery_soc=round(soc, 1),
            battery_temp_c=round(temp, 2),
            cooling_state="OFF" if self.cooling_override else ("DEGRADED" if self.cooling_efficiency < 1.0 else "NORMAL"),
            is_affected=self.is_affected,
            active_event=self.active_event
        )


class FleetSimulationEngine:
    """Orchestrates multi-charger fleet simulation and shared grid feeder coupling."""

    @staticmethod
    def run_fleet(scenario: FleetScenario, seed: Optional[int] = None) -> FleetSimulationRun:
        """Executes a deterministic multi-charger fleet simulation."""
        chosen_seed = seed if seed is not None else scenario.seed
        rng = np.random.RandomState(chosen_seed)

        # Validate charger count (10 to 50)
        charger_count = max(10, min(50, scenario.charger_count))
        duration = max(10.0, scenario.duration_seconds)

        # Initialize grid feeder digital twin
        feeder = GridFeederModel(scenario.feeder_config)

        # Instantiate fleet charger agents with realistic initial conditions
        chargers: List[ChargerAgent] = []
        for i in range(1, charger_count + 1):
            chg_id = f"CHG-{i:02d}"
            init_soc = float(rng.uniform(20.0, 75.0))
            init_temp = float(rng.uniform(24.0, 27.0))
            nominal_current = float(rng.choice([40.0, 60.0, 80.0, 100.0]))
            chargers.append(ChargerAgent(chg_id, init_soc, init_temp, nominal_current))

        # Check enabled defenses
        has_current_cap = "FLEET_CURRENT_CAP_70A" in scenario.enabled_defenses
        has_dynamic_load_management = "DYNAMIC_LOAD_MANAGEMENT" in scenario.enabled_defenses
        fleet_cap = 70.0 if has_current_cap else None

        time_slices: List[FleetTimeSlice] = []
        affected_chargers_set = set()
        overload_duration = 0.0
        peak_fleet_power = 0.0
        peak_feeder_loading = 0.0
        min_feeder_voltage = scenario.feeder_config.nominal_voltage_v

        # Sort scheduled events by timestamp
        scheduled_events = sorted(scenario.events, key=lambda e: e.get("timestamp", 0.0))

        # Simulation loop (1.0s time steps)
        steps = int(duration)
        for t_int in range(steps + 1):
            t = float(t_int)

            # Process scheduled cyber events at current time step
            for ev in scheduled_events:
                ev_time = float(ev.get("timestamp", 0.0))
                if abs(t - ev_time) < 0.5:
                    target = ev.get("target_charger_id", "ALL")
                    event_type = ev.get("event_type", "CHANGE_CURRENT_LIMIT")
                    params = ev.get("parameters", {})

                    target_agents: List[ChargerAgent] = []
                    if target == "ALL":
                        target_agents = chargers
                    elif isinstance(target, list):
                        target_agents = [c for c in chargers if c.charger_id in target]
                    else:
                        target_agents = [c for c in chargers if c.charger_id == target]

                    for ag in target_agents:
                        ag.is_affected = True
                        ag.active_event = event_type
                        affected_chargers_set.add(ag.charger_id)

                        if event_type == "CHANGE_CURRENT_LIMIT":
                            requested_i = float(params.get("requested_current", 150.0))
                            ag.requested_current_a = requested_i
                        elif event_type == "COOLING_OVERRIDE":
                            ag.cooling_override = True
                        elif event_type == "MALICIOUS_FIRMWARE_UPDATE":
                            ag.state_machine.trigger_fault("Malicious firmware payload tripped EVSE")
                        elif event_type == "COORDINATED_DEMAND_SPIKE":
                            ag.requested_current_a = 150.0

            # Dynamic Load Management adjustment if feeder approaches warning threshold
            step_fleet_cap = fleet_cap
            if has_dynamic_load_management:
                # Estimate current potential load; if > 75%, aggressively throttle non-critical chargers
                est_power = sum(c.requested_current_a * 400.0 / 1000.0 for c in chargers)
                if (est_power / scenario.feeder_config.capacity_kw) > 0.75:
                    step_fleet_cap = min(step_fleet_cap or 150.0, 55.0)

            # Step each charger agent
            charger_snapshots: List[ChargerFleetSummary] = []
            step_power_kw = 0.0
            step_current_a = 0.0
            active_count = 0
            faulted_count = 0

            for ag in chargers:
                snap = ag.step(dt=1.0, fleet_current_cap=step_fleet_cap)
                charger_snapshots.append(snap)
                step_power_kw += snap.power_kw
                step_current_a += snap.current_a
                if snap.state == "CHARGING" and snap.current_a > 1.0:
                    active_count += 1
                elif snap.state == "FAULT":
                    faulted_count += 1

            # Step grid feeder digital twin
            feeder_metrics = feeder.evaluate_step(step_power_kw, step_current_a)
            feeder_loading_pct = feeder_metrics["feeder_loading_pct"]
            feeder_v = feeder_metrics["feeder_voltage_v"]
            feeder_status = feeder_metrics["feeder_status"]

            # Update tracking aggregates
            if feeder_loading_pct > peak_feeder_loading:
                peak_feeder_loading = feeder_loading_pct
            if step_power_kw > peak_fleet_power:
                peak_fleet_power = step_power_kw
            if feeder_v < min_feeder_voltage:
                min_feeder_voltage = feeder_v
            if feeder_loading_pct >= scenario.feeder_config.warning_threshold_pct:
                overload_duration += 1.0

            time_slices.append(
                FleetTimeSlice(
                    timestamp=t,
                    total_fleet_power_kw=round(step_power_kw, 2),
                    total_fleet_current_a=round(step_current_a, 2),
                    feeder_loading_pct=round(feeder_loading_pct, 2),
                    feeder_voltage_v=round(feeder_v, 2),
                    feeder_status=feeder_status,
                    active_chargers_count=active_count,
                    faulted_chargers_count=faulted_count,
                    chargers=charger_snapshots
                )
            )

        run_id = f"RUN-FLEET-{uuid.uuid4().hex[:8].upper()}"

        return FleetSimulationRun(
            run_id=run_id,
            fleet_scenario_id=scenario.fleet_scenario_id,
            charger_count=charger_count,
            feeder_capacity_kw=scenario.feeder_config.capacity_kw,
            peak_fleet_power_kw=round(peak_fleet_power, 2),
            peak_feeder_loading_pct=round(peak_feeder_loading, 2),
            min_feeder_voltage_v=round(min_feeder_voltage, 2),
            overload_duration_seconds=round(overload_duration, 1),
            affected_chargers=sorted(list(affected_chargers_set)),
            time_slices=time_slices,
            summary={
                "feeder_status": "CRITICAL_OVERLOAD" if peak_feeder_loading >= scenario.feeder_config.critical_threshold_pct else (
                    "WARNING" if peak_feeder_loading >= scenario.feeder_config.warning_threshold_pct else "NORMAL"
                ),
                "total_energy_kwh": round(sum(s.total_fleet_power_kw for s in time_slices) / 3600.0, 2),
                "grid_sag_severity": "HIGH" if min_feeder_voltage < (scenario.feeder_config.nominal_voltage_v * 0.90) else "LOW"
            }
        )

    @staticmethod
    def get_predefined_fleet_scenarios() -> List[FleetScenario]:
        """Returns standard predefined fleet scenarios for demonstration and testing."""
        return [
            FleetScenario(
                fleet_scenario_id="FLEET-NORM-01",
                name="Nominal Fleet Operation (20 Chargers)",
                description="20 chargers operating at standard nominal currents (40A-80A). Total demand remains well within the 800 kW feeder capacity (~52% loading).",
                charger_count=20,
                duration_seconds=60.0,
                seed=101,
                feeder_config=FeederConfig(capacity_kw=800.0, nominal_voltage_v=400.0),
                events=[],
                enabled_defenses=[]
            ),
            FleetScenario(
                fleet_scenario_id="FLEET-UNEVEN-01",
                name="Uneven Fleet Charging Demand (24 Chargers)",
                description="Mixed commercial plaza charging with high variance: 8 fast chargers drawing 100A and 16 trickle chargers drawing 40A. Feeder loading reaches 76% without threshold breach.",
                charger_count=24,
                duration_seconds=60.0,
                seed=102,
                feeder_config=FeederConfig(capacity_kw=800.0, nominal_voltage_v=400.0),
                events=[],
                enabled_defenses=[]
            ),
            FleetScenario(
                fleet_scenario_id="FLEET-SINGLE-ATK-01",
                name="Targeted Single-Charger Attack (CHG-05)",
                description="Single charger CHG-05 targeted at t=15s with an unauthorized 150A overcurrent command and cooling lockout. CHG-05 overheats and trips to FAULT, while the remaining 19 chargers continue normally.",
                charger_count=20,
                duration_seconds=60.0,
                seed=103,
                feeder_config=FeederConfig(capacity_kw=800.0, nominal_voltage_v=400.0),
                events=[
                    {
                        "timestamp": 15.0,
                        "target_charger_id": "CHG-05",
                        "event_type": "CHANGE_CURRENT_LIMIT",
                        "parameters": {"requested_current": 150.0}
                    },
                    {
                        "timestamp": 16.0,
                        "target_charger_id": "CHG-05",
                        "event_type": "COOLING_OVERRIDE",
                        "parameters": {"cooling_efficiency": 0.0}
                    }
                ],
                enabled_defenses=[]
            ),
            FleetScenario(
                fleet_scenario_id="FLEET-COORD-ATK-01",
                name="Coordinated Multi-Charger Demand Surge (Critical Overload)",
                description="Coordinated cyberattack at t=15s simultaneously commanding 16 chargers to maximum 150A overcurrent. Total fleet demand surges to 960 kW (120% feeder overload), inducing severe voltage sag down to 348V.",
                charger_count=20,
                duration_seconds=60.0,
                seed=104,
                feeder_config=FeederConfig(capacity_kw=800.0, nominal_voltage_v=400.0),
                events=[
                    {
                        "timestamp": 15.0,
                        "target_charger_id": [f"CHG-{i:02d}" for i in range(1, 17)],
                        "event_type": "CHANGE_CURRENT_LIMIT",
                        "parameters": {"requested_current": 150.0}
                    }
                ],
                enabled_defenses=[]
            ),
            FleetScenario(
                fleet_scenario_id="FLEET-CSMS-OVERRIDE-01",
                name="Compromised CSMS Broadcast Override (25 Chargers)",
                description="Rogue central management system broadcasts uncoordinated 140A charging rate limits to all 25 chargers across the charging depot.",
                charger_count=25,
                duration_seconds=60.0,
                seed=105,
                feeder_config=FeederConfig(capacity_kw=900.0, nominal_voltage_v=400.0),
                events=[
                    {
                        "timestamp": 12.0,
                        "target_charger_id": "ALL",
                        "event_type": "CHANGE_CURRENT_LIMIT",
                        "parameters": {"requested_current": 140.0}
                    }
                ],
                enabled_defenses=[]
            ),
            FleetScenario(
                fleet_scenario_id="FLEET-DEFENDED-01",
                name="Defended Coordinated Demand Surge (Dynamic Clamping)",
                description="Same coordinated demand surge as FLEET-COORD-ATK-01, but with active Fleet Current Clamping (70A Max) and Dynamic Load Management enabled. Feeder loading is held safely below 74%, protecting grid stability.",
                charger_count=20,
                duration_seconds=60.0,
                seed=104,
                feeder_config=FeederConfig(capacity_kw=800.0, nominal_voltage_v=400.0),
                events=[
                    {
                        "timestamp": 15.0,
                        "target_charger_id": [f"CHG-{i:02d}" for i in range(1, 17)],
                        "event_type": "CHANGE_CURRENT_LIMIT",
                        "parameters": {"requested_current": 150.0}
                    }
                ],
                enabled_defenses=["FLEET_CURRENT_CAP_70A", "DYNAMIC_LOAD_MANAGEMENT"]
            )
        ]
