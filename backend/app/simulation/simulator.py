"""
Deterministic Simulation Engine (Features F03, F04, F06-F16, F23, F39).
Executes scenario events, steps state machines and physical models, logs telemetry,
applies deterministic noise and clock skew, applies active simulated defenses,
computes digital twin physics residuals, and guarantees seeded bitwise-reproducible outcomes.
"""

import uuid
import numpy as np
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any

from backend.app.core.config import settings
from backend.app.core.guard import SafeByDesignGuard
from backend.app.schemas.scenario import ScenarioSchema
from backend.app.schemas.events import SimulatedEventSchema
from backend.app.schemas.telemetry import TelemetryTimeSlice
from backend.app.schemas.simulation import SimulationRunResponse, ThresholdCrossing
from backend.app.schemas.defense import DefenseConfiguration
from backend.app.simulation.state_machine import EVChargerStateMachine, ChargerState
from backend.app.simulation.battery_model import BatteryBMSModel
from backend.app.simulation.thermal_model import ThermalModel
from backend.app.simulation.defenses import DefenseEngine


class SimulationEngine:

    @staticmethod
    def run(
        scenario: ScenarioSchema,
        seed: Optional[int] = None,
        omitted_event_id: Optional[str] = None,
        custom_defenses: Optional[DefenseConfiguration] = None,
        cyber_offset_override: Optional[float] = None,
        telemetry_offset_override: Optional[float] = None,
        sensor_noise_override: Optional[float] = None
    ) -> SimulationRunResponse:
        """
        Executes a deterministic simulation of the EV charging session.
        If omitted_event_id is provided, skips that specific event (Counterfactual Replay).
        Applies configurable deterministic noise, clock offsets, and active defenses.
        """
        chosen_seed = seed if seed is not None else scenario.default_seed
        SafeByDesignGuard.validate_simulation_parameters(chosen_seed, scenario.duration_seconds)

        # Initialize deterministic RNG
        rng = np.random.RandomState(chosen_seed)

        # Resolve noise and clock skew parameters
        sensor_noise_std = sensor_noise_override if sensor_noise_override is not None else scenario.sensor_noise_std
        cyber_offset = cyber_offset_override if cyber_offset_override is not None else scenario.cyber_timestamp_offset
        telem_offset = telemetry_offset_override if telemetry_offset_override is not None else scenario.telemetry_timestamp_offset
        jitter_std = scenario.measurement_jitter_std

        # Initialize defenses
        active_defense_config = custom_defenses or scenario.defense_config or DefenseConfiguration()
        defense_engine = DefenseEngine(active_defense_config)

        # Initialize subsystem models
        state_machine = EVChargerStateMachine(hardware_limit_a=settings.CHARGER_HARDWARE_MAX_CURRENT)
        battery = BatteryBMSModel(
            capacity_kwh=settings.BATTERY_CAPACITY_KWH,
            nominal_voltage=settings.BATTERY_NOMINAL_VOLTAGE,
            internal_resistance_ohm=settings.BATTERY_INTERNAL_RESISTANCE,
            initial_soc=settings.BATTERY_INITIAL_SOC,
            max_voltage_v=settings.VOLTAGE_MAX_LIMIT
        )
        thermal = ThermalModel(
            c_thermal_j_k=settings.THERMAL_HEAT_CAPACITY,
            r_thermal_k_w=settings.THERMAL_RESISTANCE_AMBIENT,
            ambient_temp_c=settings.AMBIENT_TEMPERATURE,
            initial_temp_c=settings.AMBIENT_TEMPERATURE,
            warning_temp_c=settings.TEMP_WARNING_THRESHOLD,
            critical_temp_c=settings.TEMP_CRITICAL_THRESHOLD
        )
        thermal.sensor_noise_sigma = sensor_noise_std

        # Digital Twin Observer for Physics Consistency (Feature F23)
        # Calculates ideal expected temperature based strictly on current and baseline cooling
        twin_temp_c = settings.AMBIENT_TEMPERATURE

        dt = 1.0  # 1-second simulation step
        total_steps = int(scenario.duration_seconds / dt)

        # Prepare active events with clock skew if configured
        active_events: List[SimulatedEventSchema] = []
        for ev in scenario.scheduled_events:
            SafeByDesignGuard.validate_event(ev.model_dump())
            if omitted_event_id and ev.event_id == omitted_event_id:
                continue  # Skip for counterfactual run

            # Apply cyber clock offset if configured (Feature F04)
            ev_copy = ev.model_copy()
            if cyber_offset != 0.0:
                ev_copy.timestamp = max(0.0, round(ev.timestamp + cyber_offset, 2))
            active_events.append(ev_copy)

        # Sort events chronologically
        sorted_events = sorted(active_events, key=lambda e: e.timestamp)
        event_queue = list(sorted_events)

        telemetry_slices: List[TelemetryTimeSlice] = []
        threshold_crossings: List[ThresholdCrossing] = []

        peak_current = 0.0
        peak_temperature = settings.AMBIENT_TEMPERATURE
        fault_triggered = False

        warning_temp_crossed = False
        critical_temp_crossed = False
        warning_current_crossed = False

        can_spoofed_current_val: Optional[float] = None

        # Simulation loop
        for step in range(total_steps + 1):
            t = float(step * dt)

            # 1. Process scheduled events that occur at this second
            while event_queue and event_queue[0].timestamp <= t:
                curr_event = event_queue.pop(0)
                ev_type = curr_event.event_type
                details = curr_event.details

                # Defense Check 1: Pre-event mitigation inspection (F39)
                is_allowed, denial_reason = defense_engine.inspect_event(curr_event, t)
                if not is_allowed:
                    # Event blocked by active simulated defense (e.g., unauthorized check or rate limit)
                    continue

                if ev_type == "START_TRANSACTION":
                    req_curr = float(details.get("requested_current", settings.CHARGER_DEFAULT_REQUESTED_CURRENT))
                    req_curr = defense_engine.apply_current_cap(req_curr, t)
                    state_machine.authorize()
                    state_machine.start_charging(req_curr)

                elif ev_type == "STOP_TRANSACTION":
                    state_machine.stop_charging(details.get("reason", "Normal completion"))

                elif ev_type in ("CHANGE_CURRENT_LIMIT", "SET_CHARGING_PROFILE"):
                    new_limit = float(details.get("current_limit", details.get("requested_current", 80.0)))
                    new_limit = defense_engine.apply_current_cap(new_limit, t)
                    state_machine.set_requested_current(new_limit)

                elif ev_type == "BMS_OVERRIDE_ATTEMPT":
                    override = bool(details.get("override_active", True))
                    state_machine.set_bms_override(override)
                    if "current_limit" in details:
                        new_limit = float(details["current_limit"])
                        new_limit = defense_engine.apply_current_cap(new_limit, t)
                        state_machine.set_requested_current(new_limit)

                elif ev_type in ("COOLING_OVERRIDE", "DISABLE_COOLING"):
                    factor = float(details.get("cooling_factor", 0.0))
                    thermal.set_cooling_degradation(factor)

                elif ev_type == "SENSOR_INJECT_FAULT":
                    fault_type = details.get("fault_type", "stuck")
                    param = float(details.get("parameter", 0.0))
                    thermal.inject_sensor_fault(fault_type, param)

                elif ev_type == "SENSOR_DRIFT":
                    drift_rate = float(details.get("drift_rate_c_per_sec", 0.25))
                    thermal.inject_sensor_fault("drift", drift_rate)

                elif ev_type == "SENSOR_STUCK":
                    stuck_val = float(details.get("stuck_value", 28.0))
                    thermal.inject_sensor_fault("stuck", stuck_val)

                elif ev_type == "SENSOR_SPIKE":
                    spike_val = float(details.get("spike_value", 85.0))
                    thermal.inject_sensor_fault("spike", spike_val)

                elif ev_type == "SENSOR_DROPOUT":
                    active = bool(details.get("active", True))
                    thermal.inject_sensor_fault("dropout", 1.0 if active else 0.0)

                elif ev_type == "CAN_SPOOF_TEMPERATURE":
                    spoofed_val = float(details.get("spoofed_temperature", details.get("temperature", 22.0)))
                    thermal.inject_sensor_fault("can_spoof", spoofed_val)

                elif ev_type == "CAN_SPOOF_CURRENT":
                    can_curr = float(details.get("requested_current", details.get("current", 140.0)))
                    can_spoofed_current_val = can_curr
                    capped_curr = defense_engine.apply_current_cap(can_curr, t)
                    state_machine.set_requested_current(capped_curr)

                elif ev_type == "EMERGENCY_STOP":
                    state_machine.trigger_fault("Emergency stop button depressed")

                elif ev_type == "FIRMWARE_UPDATE":
                    if details.get("malicious_tamper", False):
                        state_machine.set_bms_override(True)
                        forced_curr = float(details.get("forced_current", 150.0))
                        forced_curr = defense_engine.apply_current_cap(forced_curr, t)
                        state_machine.set_requested_current(forced_curr)

            # 2. Dynamic BMS feedback limit calculation
            bms_recommended_limit = battery.compute_bms_recommended_limit(thermal.temperature_c)
            state_machine.set_bms_limit(bms_recommended_limit)

            # 3. Resolve actual electrical current
            actual_current, limit_source = state_machine.compute_actual_current()

            # Deterministic measurement noise
            noise_sample = rng.normal(0.0, 1.0)
            jitter_sample = rng.normal(0.0, jitter_std) if jitter_std > 0 else 0.0
            measured_current = actual_current + (noise_sample * sensor_noise_std if actual_current > 0 else 0.0)

            # 4. Step battery electrical state
            v_terminal, soc, batt_flags = battery.step(actual_current, dt)

            # 5. Step physical thermal state & sensor model
            actual_temp, reported_temp, therm_metrics = thermal.step(
                current_a=actual_current,
                resistance_ohm=battery.internal_resistance_ohm,
                dt_seconds=dt,
                rng_noise=noise_sample
            )
            sensor_quality = therm_metrics.get("sensor_quality", "good")

            # 6. Digital Twin Predicted State (Feature F23 - Physics Consistency Observer)
            twin_p_heat = (actual_current ** 2) * battery.internal_resistance_ohm
            twin_p_cool = ((twin_temp_c - settings.AMBIENT_TEMPERATURE) / settings.THERMAL_RESISTANCE_AMBIENT) * 1.0
            twin_temp_c += ((twin_p_heat - twin_p_cool) / settings.THERMAL_HEAT_CAPACITY) * dt
            twin_temp_c = max(settings.AMBIENT_TEMPERATURE, min(150.0, twin_temp_c))
            temperature_residual = round(reported_temp - twin_temp_c, 2)

            # Defense Check 2: Sensor cross-checking & thermal lockout
            defense_engine.inspect_sensor(reported_temp, twin_temp_c, t)
            is_lockout = defense_engine.inspect_thermal_lockout(actual_temp, t)
            if is_lockout and state_machine.state == ChargerState.CHARGING:
                state_machine.trigger_fault(f"Thermal Lockout Active: Pack reached {actual_temp:.1f}°C")
                fault_triggered = True

            # Grid load indicator (kW)
            grid_kw = (v_terminal * actual_current / 1000.0) + (1.2 if state_machine.state == ChargerState.CHARGING else 0.2)

            # 7. Safety trip check (BMS protective breaker)
            if actual_temp >= settings.TEMP_CRITICAL_THRESHOLD and state_machine.state == ChargerState.CHARGING:
                state_machine.trigger_fault(f"Thermal Critical Cutoff: Pack reached {actual_temp:.1f}°C")
                fault_triggered = True

                if not critical_temp_crossed:
                    critical_temp_crossed = True
                    threshold_crossings.append(ThresholdCrossing(
                        timestamp=t,
                        signal="battery_temperature",
                        threshold_type="critical",
                        threshold_value=settings.TEMP_CRITICAL_THRESHOLD,
                        observed_value=round(actual_temp, 2),
                        unit="°C",
                        description=f"CRITICAL: Battery temperature reached {actual_temp:.1f}°C. Hardware safety breaker tripped."
                    ))

            if actual_temp >= settings.TEMP_WARNING_THRESHOLD and not warning_temp_crossed:
                warning_temp_crossed = True
                threshold_crossings.append(ThresholdCrossing(
                    timestamp=t,
                    signal="battery_temperature",
                    threshold_type="warning",
                    threshold_value=settings.TEMP_WARNING_THRESHOLD,
                    observed_value=round(actual_temp, 2),
                    unit="°C",
                    description=f"WARNING: Battery temperature exceeded caution threshold of {settings.TEMP_WARNING_THRESHOLD}°C."
                ))

            if actual_current >= settings.CURRENT_WARNING_THRESHOLD and not warning_current_crossed:
                warning_current_crossed = True
                threshold_crossings.append(ThresholdCrossing(
                    timestamp=t,
                    signal="charging_current",
                    threshold_type="warning",
                    threshold_value=settings.CURRENT_WARNING_THRESHOLD,
                    observed_value=round(actual_current, 2),
                    unit="A",
                    description=f"WARNING: High current surge detected ({actual_current:.1f}A >= {settings.CURRENT_WARNING_THRESHOLD}A)."
                ))

            # Update peaks
            if actual_current > peak_current:
                peak_current = actual_current
            if actual_temp > peak_temperature:
                peak_temperature = actual_temp

            # Compute aligned timestamp if telemetry offset is active
            aligned_t = round(t - telem_offset, 2) if telem_offset != 0.0 else round(t, 2)

            # Record telemetry slice
            telemetry_slices.append(TelemetryTimeSlice(
                timestamp=round(t + jitter_sample, 2),
                aligned_timestamp=aligned_t,
                battery_temperature=round(actual_temp, 2),
                charging_current=round(actual_current, 2),
                battery_voltage=round(v_terminal, 2),
                state_of_charge=round(soc, 2),
                cooling_power=round(therm_metrics["p_cool_w"], 1),
                sensor_temperature=round(reported_temp, 2),
                reported_current=round(measured_current, 2),
                sensor_quality=sensor_quality,
                predicted_temperature=round(twin_temp_c, 2),
                temperature_residual=temperature_residual,
                can_spoofed_temperature=round(thermal.can_spoofed_temp, 2) if thermal.can_spoofed_temp is not None else None,
                can_spoofed_current=round(can_spoofed_current_val, 2) if can_spoofed_current_val is not None else None,
                grid_load=round(grid_kw, 2),
                charger_state=state_machine.state.value
            ))

        run_id = f"RUN-{uuid.uuid4().hex[:8].upper()}"
        return SimulationRunResponse(
            run_id=run_id,
            scenario_id=scenario.scenario_id,
            scenario_name=scenario.name,
            scenario_family=scenario.family,
            seed=chosen_seed,
            duration_seconds=scenario.duration_seconds,
            created_at=datetime.now(timezone.utc).isoformat(),
            status="COMPLETED",
            is_counterfactual=bool(omitted_event_id is not None),
            omitted_event_id=omitted_event_id,
            events=active_events,
            telemetry=telemetry_slices,
            peak_current=round(peak_current, 2),
            peak_temperature=round(peak_temperature, 2),
            final_soc=round(battery.soc, 2),
            fault_triggered=fault_triggered or (state_machine.state == ChargerState.FAULT),
            threshold_crossings=threshold_crossings,
            defense_interventions=defense_engine.interventions,
            cyber_timestamp_offset=cyber_offset,
            telemetry_timestamp_offset=telem_offset,
            sensor_noise_std=sensor_noise_std
        )
