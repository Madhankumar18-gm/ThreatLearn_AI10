"""
Tests for Physics Models and State Machine (Features F06, F07, F08, Acceptance Criteria 4, 5, 6).
"""

import pytest
from backend.app.simulation.state_machine import EVChargerStateMachine, ChargerState
from backend.app.simulation.battery_model import BatteryBMSModel
from backend.app.simulation.thermal_model import ThermalModel
from backend.app.scenarios.library import SCENARIOS_MAP
from backend.app.simulation.simulator import SimulationEngine


def test_charger_state_machine_transitions():
    """Criteria 4: Charger state transitions are validated."""
    sm = EVChargerStateMachine(hardware_limit_a=150.0)
    assert sm.state == ChargerState.IDLE

    # Valid forward transitions
    assert sm.authorize() is True
    assert sm.state == ChargerState.AUTHORIZED

    assert sm.start_charging(80.0) is True
    assert sm.state == ChargerState.CHARGING

    # Stop back to idle
    assert sm.stop_charging() is True
    assert sm.state == ChargerState.IDLE

    # Fault transition from any state
    sm.trigger_fault("Overcurrent detected")
    assert sm.state == ChargerState.FAULT
    curr, _ = sm.compute_actual_current()
    assert curr == 0.0

    # Cannot charge while faulted
    assert sm.start_charging(50.0) is False

    # Reset recovery
    assert sm.reset_fault() is True
    assert sm.state == ChargerState.IDLE


def test_charging_current_respects_model_limits():
    """Criteria 5: Charging current respects model limits."""
    sm = EVChargerStateMachine(hardware_limit_a=150.0)
    sm.state = ChargerState.CHARGING

    # Requested within limits
    sm.set_requested_current(80.0)
    sm.set_bms_limit(100.0)
    curr, src = sm.compute_actual_current()
    assert curr == 80.0

    # Requested exceeds BMS limit
    sm.set_requested_current(120.0)
    sm.set_bms_limit(90.0)
    curr, src = sm.compute_actual_current()
    assert curr == 90.0
    assert src == "bms_limit"

    # Requested exceeds hardware ceiling
    sm.set_requested_current(200.0)
    sm.set_bms_limit(200.0)
    curr, src = sm.compute_actual_current()
    assert curr == 150.0
    assert src == "hardware_limit"


def test_battery_and_thermal_values_within_numerical_bounds():
    """Criteria 6: Battery and thermal values remain within defined numerical bounds."""
    battery = BatteryBMSModel(capacity_kwh=60.0, initial_soc=30.0)
    thermal = ThermalModel(initial_temp_c=25.0)

    # Step simulation under high load for 60 seconds
    for _ in range(60):
        v_terminal, soc, _ = battery.step(current_a=100.0, dt_seconds=1.0)
        temp, sensor_temp, _ = thermal.step(current_a=100.0, resistance_ohm=battery.internal_resistance_ohm, dt_seconds=1.0)

        assert 0.0 <= soc <= 100.0, f"SoC out of bounds: {soc}"
        assert 300.0 <= v_terminal <= 470.0, f"Voltage out of bounds: {v_terminal}"
        assert 25.0 <= temp <= 150.0, f"Temperature out of bounds: {temp}"


def test_all_scenarios_execute_within_physical_bounds():
    """Verifies that every scenario in library runs safely without numerical divergence."""
    for s_id, scenario in SCENARIOS_MAP.items():
        res = SimulationEngine.run(scenario)
        assert res.peak_current >= 0.0
        assert res.peak_temperature >= 25.0
        assert 0.0 <= res.final_soc <= 100.0
        assert len(res.telemetry) == int(scenario.duration_seconds) + 1
