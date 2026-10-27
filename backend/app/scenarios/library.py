"""
Scenario Library (Feature F01).
Contains 28 labelled, deterministic scenarios across the 8 primary families:
1. Normal operation
2. Attack
3. Sensor fault
4. Benign high-power event
5. Delayed attack
6. Masked attack
7. Fleet attack
8. Defended attack
"""

from typing import List, Dict
from backend.app.schemas.scenario import ScenarioSchema, GroundTruthLinkSchema
from backend.app.schemas.events import SimulatedEventSchema, GroundTruthMetadata


def build_scenario_library() -> List[ScenarioSchema]:
    scenarios: List[ScenarioSchema] = [

        # ==========================================
        # FAMILY 1: NORMAL OPERATION
        # ==========================================
        ScenarioSchema(
            scenario_id="SCN-NORM-01",
            name="Standard 80A Fast Charging Session",
            family="Normal operation",
            description="Nominal baseline DC fast charging session at 80A. Heat dissipation balances Joule heating, stabilizing pack temperature around 31°C.",
            duration_seconds=60.0,
            default_seed=101,
            components_involved=["csms_backend", "evse_controller", "power_converter", "battery_pack", "cooling_system", "temperature_sensor"],
            scheduled_events=[
                SimulatedEventSchema(
                    event_id="EVT-NORM-01-A",
                    timestamp=5.0,
                    layer="cyber_protocol",
                    component_id="csms_backend",
                    event_type="START_TRANSACTION",
                    source="csms",
                    auth_status="authorized",
                    details={"requested_current": 80.0, "rfid": "USER-VALID-781"},
                    ground_truth=GroundTruthMetadata(is_malicious=False, target_signal="charging_current", expected_delta="+80A", expected_causal=True)
                ),
                SimulatedEventSchema(
                    event_id="EVT-NORM-01-B",
                    timestamp=55.0,
                    layer="cyber_protocol",
                    component_id="csms_backend",
                    event_type="STOP_TRANSACTION",
                    source="csms",
                    auth_status="authorized",
                    details={"reason": "Normal session completion"},
                    ground_truth=GroundTruthMetadata(is_malicious=False, target_signal="charging_current", expected_delta="0A", expected_causal=True)
                )
            ],
            expected_physical_effects="Smooth current rise to 80A, moderate thermal rise from 25.0°C to ~31.0°C, linear SoC increase from 30% to ~31.8%.",
            ground_truth_links=[
                GroundTruthLinkSchema(
                    event_id="EVT-NORM-01-A",
                    target_signal="charging_current",
                    is_causal=True,
                    expected_delay_min=0.5,
                    expected_delay_max=2.0,
                    rationale="Legitimate StartTransaction causes power converter to ramp current to 80A."
                )
            ],
            expected_outcome="Session completes within all design limits; no warnings or fault trips.",
            safety_limitations="Simulation model assumes static cooling efficiency of 1.0 and constant ambient 25°C."
        ),

        ScenarioSchema(
            scenario_id="SCN-NORM-02",
            name="Low-Power Trickle Charge (30A)",
            family="Normal operation",
            description="Gentle low-amperage session representative of residential or off-peak charging. Negligible thermal buildup.",
            duration_seconds=60.0,
            default_seed=102,
            components_involved=["csms_backend", "evse_controller", "power_converter", "battery_pack", "cooling_system"],
            scheduled_events=[
                SimulatedEventSchema(
                    event_id="EVT-NORM-02-A",
                    timestamp=5.0,
                    layer="cyber_protocol",
                    component_id="csms_backend",
                    event_type="START_TRANSACTION",
                    source="csms",
                    auth_status="authorized",
                    details={"requested_current": 30.0},
                    ground_truth=GroundTruthMetadata(is_malicious=False, target_signal="charging_current", expected_delta="+30A", expected_causal=True)
                )
            ],
            expected_physical_effects="Current rises to 30A; pack temperature remains under 27°C.",
            ground_truth_links=[
                GroundTruthLinkSchema(
                    event_id="EVT-NORM-02-A",
                    target_signal="charging_current",
                    is_causal=True,
                    expected_delay_min=0.5,
                    expected_delay_max=2.0,
                    rationale="Authorized 30A command initiates trickle charge."
                )
            ],
            expected_outcome="Normal stable operation without warning threshold crossings.",
            safety_limitations="Model simplifies low-current converter efficiency curve."
        ),

        ScenarioSchema(
            scenario_id="SCN-NORM-03",
            name="High-Power Fast Charge with Active Cooling (120A)",
            family="Normal operation",
            description="Upper-range authorized DC fast charge at 120A. Higher Joule heating is effectively rejected by active cooling, remaining below 40°C.",
            duration_seconds=60.0,
            default_seed=103,
            components_involved=["csms_backend", "evse_controller", "power_converter", "battery_pack", "cooling_system"],
            scheduled_events=[
                SimulatedEventSchema(
                    event_id="EVT-NORM-03-A",
                    timestamp=4.0,
                    layer="cyber_protocol",
                    component_id="csms_backend",
                    event_type="START_TRANSACTION",
                    source="csms",
                    auth_status="authorized",
                    details={"requested_current": 120.0},
                    ground_truth=GroundTruthMetadata(is_malicious=False, target_signal="charging_current", expected_delta="+120A", expected_causal=True)
                )
            ],
            expected_physical_effects="Rapid current ramp to 120A; temperature rises to ~37.5°C, safely below 45°C warning limit.",
            ground_truth_links=[
                GroundTruthLinkSchema(
                    event_id="EVT-NORM-03-A",
                    target_signal="charging_current",
                    is_causal=True,
                    expected_delay_min=0.5,
                    expected_delay_max=2.0,
                    rationale="Authorized high-power command drives 120A output."
                )
            ],
            expected_outcome="Normal high-rate charging without threshold violations.",
            safety_limitations="Assumes constant heat exchanger radiator airflow."
        ),

        ScenarioSchema(
            scenario_id="SCN-NORM-04",
            name="User-Initiated Early Session Termination",
            family="Normal operation",
            description="Driver terminates session via EVSE touch panel after 25 seconds of nominal charging.",
            duration_seconds=60.0,
            default_seed=104,
            components_involved=["evse_controller", "power_converter", "battery_pack"],
            scheduled_events=[
                SimulatedEventSchema(
                    event_id="EVT-NORM-04-A",
                    timestamp=3.0,
                    layer="cyber_protocol",
                    component_id="csms_backend",
                    event_type="START_TRANSACTION",
                    source="csms",
                    auth_status="authorized",
                    details={"requested_current": 75.0},
                    ground_truth=GroundTruthMetadata(is_malicious=False, target_signal="charging_current", expected_delta="+75A", expected_causal=True)
                ),
                SimulatedEventSchema(
                    event_id="EVT-NORM-04-B",
                    timestamp=25.0,
                    layer="controller",
                    component_id="evse_controller",
                    event_type="STOP_TRANSACTION",
                    source="operator",
                    auth_status="authorized",
                    details={"reason": "Driver button press"},
                    ground_truth=GroundTruthMetadata(is_malicious=False, target_signal="charging_current", expected_delta="0A", expected_causal=True)
                )
            ],
            expected_physical_effects="Current steps to 75A, then returns to 0A at t=25s. Temperature begins cooling back toward ambient.",
            ground_truth_links=[
                GroundTruthLinkSchema(
                    event_id="EVT-NORM-04-B",
                    target_signal="charging_current",
                    is_causal=True,
                    expected_delay_min=0.5,
                    expected_delay_max=2.0,
                    rationale="Driver stop signal commands converter current to zero."
                )
            ],
            expected_outcome="Clean shutdown with thermal decay.",
            safety_limitations="Mechanical contactor de-energization arc dynamics omitted."
        ),

        # ==========================================
        # FAMILY 2: ATTACK
        # ==========================================
        ScenarioSchema(
            scenario_id="SCN-ATK-01",
            name="Unauthorized Current Limit Override (150A)",
            family="Attack",
            description="Man-in-the-middle attacker injects an unauthorized SetChargingProfile message raising current to hardware ceiling (150A), driving rapid thermal escalation.",
            duration_seconds=60.0,
            default_seed=201,
            components_involved=["csms_backend", "evse_controller", "power_converter", "battery_pack", "cooling_system"],
            scheduled_events=[
                SimulatedEventSchema(
                    event_id="EVT-ATK-01-A",
                    timestamp=5.0,
                    layer="cyber_protocol",
                    component_id="csms_backend",
                    event_type="START_TRANSACTION",
                    source="csms",
                    auth_status="authorized",
                    details={"requested_current": 60.0},
                    ground_truth=GroundTruthMetadata(is_malicious=False, target_signal="charging_current", expected_delta="+60A", expected_causal=True)
                ),
                SimulatedEventSchema(
                    event_id="EVT-ATK-01-B",
                    timestamp=15.0,
                    layer="cyber_protocol",
                    component_id="evse_controller",
                    event_type="CHANGE_CURRENT_LIMIT",
                    source="man_in_the_middle",
                    auth_status="unauthorized",
                    details={"current_limit": 150.0, "exploit_tag": "OCPP-INJECT-01"},
                    ground_truth=GroundTruthMetadata(
                        is_malicious=True,
                        target_signal="battery_temperature",
                        expected_delta="+16°C",
                        expected_causal=True,
                        rationale="Unauthorized 150A command forces power converter to max current, quadrupling Joule heating."
                    )
                )
            ],
            expected_physical_effects="Current jumps from 60A to 150A at t=15s. Temperature surges past 45°C warning limit by t=42s.",
            ground_truth_links=[
                GroundTruthLinkSchema(
                    event_id="EVT-ATK-01-B",
                    target_signal="charging_current",
                    is_causal=True,
                    expected_delay_min=0.5,
                    expected_delay_max=2.0,
                    rationale="Unauthorized packet alters controller current setpoint."
                ),
                GroundTruthLinkSchema(
                    event_id="EVT-ATK-01-B",
                    target_signal="battery_temperature",
                    is_causal=True,
                    expected_delay_min=5.0,
                    expected_delay_max=30.0,
                    rationale="Overcurrent causes sustained excessive Joule dissipation."
                )
            ],
            expected_outcome="Thermal warning threshold crossed; counterfactual replay proves 150A injection is the sole root cause.",
            safety_limitations="Simplified thermal equation. In real vehicle, contactors or onboard fuses would isolate pack."
        ),

        ScenarioSchema(
            scenario_id="SCN-ATK-02",
            name="Dual-Vector Rogue Overcurrent with Cooling Lockout",
            family="Attack",
            description="Combined attack injecting 150A overcurrent while shutting down active cooling valves (cooling_factor=0.0). Results in thermal critical trip at 60°C.",
            duration_seconds=60.0,
            default_seed=202,
            components_involved=["evse_controller", "power_converter", "battery_pack", "cooling_system", "bms"],
            scheduled_events=[
                SimulatedEventSchema(
                    event_id="EVT-ATK-02-A",
                    timestamp=4.0,
                    layer="cyber_protocol",
                    component_id="csms_backend",
                    event_type="START_TRANSACTION",
                    source="csms",
                    auth_status="authorized",
                    details={"requested_current": 70.0},
                    ground_truth=GroundTruthMetadata(is_malicious=False)
                ),
                SimulatedEventSchema(
                    event_id="EVT-ATK-02-B",
                    timestamp=12.0,
                    layer="cyber_protocol",
                    component_id="evse_controller",
                    event_type="CHANGE_CURRENT_LIMIT",
                    source="local_attacker",
                    auth_status="unauthorized",
                    details={"current_limit": 150.0},
                    ground_truth=GroundTruthMetadata(is_malicious=True, target_signal="charging_current", expected_causal=True)
                ),
                SimulatedEventSchema(
                    event_id="EVT-ATK-02-C",
                    timestamp=14.0,
                    layer="controller",
                    component_id="cooling_system",
                    event_type="COOLING_OVERRIDE",
                    source="local_attacker",
                    auth_status="unauthorized",
                    details={"cooling_factor": 0.0, "action": "suppress_pumps"},
                    ground_truth=GroundTruthMetadata(
                        is_malicious=True,
                        target_signal="battery_temperature",
                        expected_delta=">60°C Critical Trip",
                        expected_causal=True
                    )
                )
            ],
            expected_physical_effects="Without cooling, 150A current drives temperature past 60°C, causing BMS critical hardware trip.",
            ground_truth_links=[
                GroundTruthLinkSchema(
                    event_id="EVT-ATK-02-C",
                    target_signal="battery_temperature",
                    is_causal=True,
                    expected_delay_min=5.0,
                    expected_delay_max=35.0,
                    rationale="Cooling suppression prevents heat rejection during overcurrent."
                )
            ],
            expected_outcome="BMS critical shutdown triggered; fault recorded.",
            safety_limitations="Model stops current upon fault trip; real pack may suffer internal cell degradation."
        ),

        ScenarioSchema(
            scenario_id="SCN-ATK-03",
            name="Firmware Flash Tamper - BMS Limit Bypass",
            family="Attack",
            description="Attacker delivers a malicious firmware update to the EVSE controller that disables BMS safety handshake and forces 140A output.",
            duration_seconds=60.0,
            default_seed=203,
            components_involved=["evse_controller", "bms", "power_converter", "battery_pack"],
            scheduled_events=[
                SimulatedEventSchema(
                    event_id="EVT-ATK-03-A",
                    timestamp=3.0,
                    layer="cyber_protocol",
                    component_id="csms_backend",
                    event_type="START_TRANSACTION",
                    source="csms",
                    auth_status="authorized",
                    details={"requested_current": 60.0}
                ),
                SimulatedEventSchema(
                    event_id="EVT-ATK-03-B",
                    timestamp=18.0,
                    layer="controller",
                    component_id="evse_controller",
                    event_type="FIRMWARE_UPDATE",
                    source="man_in_the_middle",
                    auth_status="spoofed",
                    details={"malicious_tamper": True, "forced_current": 140.0, "bypass_bms": True},
                    ground_truth=GroundTruthMetadata(is_malicious=True, target_signal="charging_current", expected_causal=True)
                )
            ],
            expected_physical_effects="Current rises from 60A to 140A; pack thermal rise accelerates past 45°C.",
            ground_truth_links=[
                GroundTruthLinkSchema(
                    event_id="EVT-ATK-03-B",
                    target_signal="charging_current",
                    is_causal=True,
                    expected_delay_min=0.5,
                    expected_delay_max=3.0,
                    rationale="Tampered firmware overrides controller limits."
                )
            ],
            expected_outcome="Warning threshold reached; counterfactual proves firmware event created overcurrent.",
            safety_limitations="Firmware integrity verification checks are abstracted."
        ),

        ScenarioSchema(
            scenario_id="SCN-ATK-04",
            name="Spoofed Authorization Burst Injection",
            family="Attack",
            description="Rogue diagnostic tool injects a spoofed maximum-rate authorization burst during an idle state.",
            duration_seconds=60.0,
            default_seed=204,
            components_involved=["evse_controller", "power_converter", "grid_interface"],
            scheduled_events=[
                SimulatedEventSchema(
                    event_id="EVT-ATK-04-A",
                    timestamp=10.0,
                    layer="cyber_protocol",
                    component_id="evse_controller",
                    event_type="START_TRANSACTION",
                    source="diagnostic_tool",
                    auth_status="spoofed",
                    details={"requested_current": 145.0, "mode": "raw_test"},
                    ground_truth=GroundTruthMetadata(is_malicious=True, target_signal="charging_current", expected_causal=True)
                )
            ],
            expected_physical_effects="Abrupt transition from 0A directly to 145A, producing sudden 58 kW grid surge.",
            ground_truth_links=[
                GroundTruthLinkSchema(
                    event_id="EVT-ATK-04-A",
                    target_signal="charging_current",
                    is_causal=True,
                    expected_delay_min=0.5,
                    expected_delay_max=2.0,
                    rationale="Spoofed authorization forces immediate high current output."
                )
            ],
            expected_outcome="Unscheduled session detected; severe grid load spike.",
            safety_limitations="Pilot wire electrical proximity pin check assumed bypassed."
        ),

        # ==========================================
        # FAMILY 3: SENSOR FAULT
        # ==========================================
        ScenarioSchema(
            scenario_id="SCN-FLT-01",
            name="Stuck Thermistor Sensor Artifact (Frozen at 25°C)",
            family="Sensor fault",
            description="The temperature sensor hardware ADC freezes at 25.0°C at t=15s. Physical pack heats normally to ~32°C. No physical attack has occurred.",
            duration_seconds=60.0,
            default_seed=301,
            components_involved=["temperature_sensor", "evse_controller", "battery_pack"],
            scheduled_events=[
                SimulatedEventSchema(
                    event_id="EVT-FLT-01-A",
                    timestamp=4.0,
                    layer="cyber_protocol",
                    component_id="csms_backend",
                    event_type="START_TRANSACTION",
                    source="csms",
                    auth_status="authorized",
                    details={"requested_current": 80.0}
                ),
                SimulatedEventSchema(
                    event_id="EVT-FLT-01-B",
                    timestamp=15.0,
                    layer="sensor",
                    component_id="temperature_sensor",
                    event_type="SENSOR_INJECT_FAULT",
                    source="sensor_hardware",
                    auth_status="authorized",
                    details={"fault_type": "stuck", "parameter": 25.0},
                    ground_truth=GroundTruthMetadata(
                        is_malicious=False,
                        target_signal="sensor_temperature",
                        expected_delta="Frozen at 25°C",
                        expected_causal=True,
                        rationale="Sensor hardware malfunction; physical temperature continues normal trajectory."
                    )
                )
            ],
            expected_physical_effects="Actual battery temperature rises to ~32°C; reported sensor temperature stays flat at 25.0°C.",
            ground_truth_links=[
                GroundTruthLinkSchema(
                    event_id="EVT-FLT-01-B",
                    target_signal="sensor_temperature",
                    is_causal=True,
                    expected_delay_min=0.0,
                    expected_delay_max=1.0,
                    rationale="Hardware fault freezes ADC sensor reading."
                )
            ],
            expected_outcome="Correlation engine must distinguish sensor telemetry artifact from actual physical cyber attack.",
            safety_limitations="Sensor failure does not cause physical overheating in this benign session."
        ),

        ScenarioSchema(
            scenario_id="SCN-FLT-02",
            name="Positive Sensor Offset (+18°C Calibration Drift)",
            family="Sensor fault",
            description="Grounding glitch introduces an instantaneous +18°C positive offset to sensor output, creating a fake high-temperature alarm.",
            duration_seconds=60.0,
            default_seed=302,
            components_involved=["temperature_sensor", "battery_pack"],
            scheduled_events=[
                SimulatedEventSchema(
                    event_id="EVT-FLT-02-A",
                    timestamp=5.0,
                    layer="cyber_protocol",
                    component_id="csms_backend",
                    event_type="START_TRANSACTION",
                    source="csms",
                    auth_status="authorized",
                    details={"requested_current": 70.0}
                ),
                SimulatedEventSchema(
                    event_id="EVT-FLT-02-B",
                    timestamp=20.0,
                    layer="sensor",
                    component_id="temperature_sensor",
                    event_type="SENSOR_INJECT_FAULT",
                    source="sensor_hardware",
                    auth_status="authorized",
                    details={"fault_type": "offset", "parameter": 18.0},
                    ground_truth=GroundTruthMetadata(is_malicious=False, target_signal="sensor_temperature", expected_causal=True)
                )
            ],
            expected_physical_effects="Sensor temperature jumps from 28°C to 46°C instantly, while actual battery temperature remains safe at 28°C.",
            ground_truth_links=[
                GroundTruthLinkSchema(
                    event_id="EVT-FLT-02-B",
                    target_signal="sensor_temperature",
                    is_causal=True,
                    expected_delay_min=0.0,
                    expected_delay_max=1.0,
                    rationale="Offset fault biases sensor reading upward."
                )
            ],
            expected_outcome="Sensor reading crosses warning threshold, but counterfactual proves physical battery temperature was unchanged.",
            safety_limitations="Model distinguishes between actual temperature and sensor reporting channel."
        ),

        ScenarioSchema(
            scenario_id="SCN-FLT-03",
            name="High-Noise Current Transducer Jitter",
            family="Sensor fault",
            description="EMI coupling causes elevated Gaussian noise in current sensor measurements without altering physical energy delivery.",
            duration_seconds=60.0,
            default_seed=303,
            components_involved=["current_sensor", "evse_controller"],
            scheduled_events=[
                SimulatedEventSchema(
                    event_id="EVT-FLT-03-A",
                    timestamp=5.0,
                    layer="cyber_protocol",
                    component_id="csms_backend",
                    event_type="START_TRANSACTION",
                    source="csms",
                    auth_status="authorized",
                    details={"requested_current": 60.0}
                ),
                SimulatedEventSchema(
                    event_id="EVT-FLT-03-B",
                    timestamp=20.0,
                    layer="sensor",
                    component_id="temperature_sensor",
                    event_type="SENSOR_INJECT_FAULT",
                    source="sensor_hardware",
                    auth_status="authorized",
                    details={"fault_type": "noise", "parameter": 2.5},
                    ground_truth=GroundTruthMetadata(is_malicious=False)
                )
            ],
            expected_physical_effects="High variance oscillations in telemetry readings; underlying thermal and battery state remain nominal.",
            ground_truth_links=[],
            expected_outcome="Noise margin rule filters out jitter; no false attack links generated.",
            safety_limitations="Illustrative noise model."
        ),

        ScenarioSchema(
            scenario_id="SCN-FLT-04",
            name="Intermittent Sensor Dropout",
            family="Sensor fault",
            description="Loose sensor connector causes brief dropouts to 0°C at t=25s, then returns to normal.",
            duration_seconds=60.0,
            default_seed=304,
            components_involved=["temperature_sensor", "battery_pack"],
            scheduled_events=[
                SimulatedEventSchema(
                    event_id="EVT-FLT-04-A",
                    timestamp=5.0,
                    layer="cyber_protocol",
                    component_id="csms_backend",
                    event_type="START_TRANSACTION",
                    source="csms",
                    auth_status="authorized",
                    details={"requested_current": 70.0}
                ),
                SimulatedEventSchema(
                    event_id="EVT-FLT-04-B",
                    timestamp=25.0,
                    layer="sensor",
                    component_id="temperature_sensor",
                    event_type="SENSOR_INJECT_FAULT",
                    source="sensor_hardware",
                    auth_status="authorized",
                    details={"fault_type": "stuck", "parameter": 0.0},
                    ground_truth=GroundTruthMetadata(is_malicious=False)
                ),
                SimulatedEventSchema(
                    event_id="EVT-FLT-04-C",
                    timestamp=35.0,
                    layer="sensor",
                    component_id="temperature_sensor",
                    event_type="SENSOR_INJECT_FAULT",
                    source="sensor_hardware",
                    auth_status="authorized",
                    details={"fault_type": "clear"},
                    ground_truth=GroundTruthMetadata(is_malicious=False)
                )
            ],
            expected_physical_effects="Sensor reading drops to 0°C for 10s then recovers; physical pack continues smooth heating.",
            ground_truth_links=[],
            expected_outcome="Sensor fault identified without labeling as cyberattack.",
            safety_limitations="Loss of signal timeout in BMS not triggered in simplified model."
        ),

        # ==========================================
        # FAMILY 4: BENIGN HIGH-POWER EVENT
        # ==========================================
        ScenarioSchema(
            scenario_id="SCN-BNG-01",
            name="Legitimate Fast Boost Request (130A)",
            family="Benign high-power event",
            description="Legitimate high-power boost requested via premium charging tier. Physical heating is elevated but completely legitimate and authorized.",
            duration_seconds=60.0,
            default_seed=401,
            components_involved=["csms_backend", "evse_controller", "power_converter", "battery_pack"],
            scheduled_events=[
                SimulatedEventSchema(
                    event_id="EVT-BNG-01-A",
                    timestamp=5.0,
                    layer="cyber_protocol",
                    component_id="csms_backend",
                    event_type="START_TRANSACTION",
                    source="csms",
                    auth_status="authorized",
                    details={"requested_current": 80.0}
                ),
                SimulatedEventSchema(
                    event_id="EVT-BNG-01-B",
                    timestamp=20.0,
                    layer="cyber_protocol",
                    component_id="csms_backend",
                    event_type="CHANGE_CURRENT_LIMIT",
                    source="csms",
                    auth_status="authorized",
                    details={"current_limit": 130.0, "tariff": "ultra_fast_tier"},
                    ground_truth=GroundTruthMetadata(
                        is_malicious=False,
                        target_signal="charging_current",
                        expected_delta="+50A",
                        expected_causal=True,
                        rationale="Authorized tariff upgrade lawfully requests 130A."
                    )
                )
            ],
            expected_physical_effects="Current steps from 80A to 130A. Pack temperature reaches ~39°C, staying safely below 45°C limit.",
            ground_truth_links=[
                GroundTruthLinkSchema(
                    event_id="EVT-BNG-01-B",
                    target_signal="charging_current",
                    is_causal=True,
                    expected_delay_min=0.5,
                    expected_delay_max=2.0,
                    rationale="Authorized tariff change increases current."
                )
            ],
            expected_outcome="Correlation engine notes high current was authorized; classified as benign operational behavior.",
            safety_limitations="Requires adequate EVSE thermal sizing."
        ),

        ScenarioSchema(
            scenario_id="SCN-BNG-02",
            name="Cold Weather Pre-Conditioning Surge (115A)",
            family="Benign high-power event",
            description="Battery management system initiates pack thermal pre-conditioning cycle with higher current draw to bring cells to optimal electrochemical range.",
            duration_seconds=60.0,
            default_seed=402,
            components_involved=["bms", "evse_controller", "power_converter", "battery_pack"],
            scheduled_events=[
                SimulatedEventSchema(
                    event_id="EVT-BNG-02-A",
                    timestamp=4.0,
                    layer="cyber_protocol",
                    component_id="csms_backend",
                    event_type="START_TRANSACTION",
                    source="csms",
                    auth_status="authorized",
                    details={"requested_current": 60.0}
                ),
                SimulatedEventSchema(
                    event_id="EVT-BNG-02-B",
                    timestamp=16.0,
                    layer="controller",
                    component_id="bms",
                    event_type="CHANGE_CURRENT_LIMIT",
                    source="bms_hardware",
                    auth_status="authorized",
                    details={"current_limit": 115.0, "reason": "preconditioning"},
                    ground_truth=GroundTruthMetadata(is_malicious=False, target_signal="charging_current", expected_causal=True)
                )
            ],
            expected_physical_effects="Current rises to 115A; gentle thermal rise accelerates favorably toward 35°C.",
            ground_truth_links=[],
            expected_outcome="Benign operational heating; no safety violation.",
            safety_limitations="Ambient temperature fixed at 25°C in illustrative model."
        ),

        ScenarioSchema(
            scenario_id="SCN-BNG-03",
            name="Dynamic Load Balancing Peak (125A)",
            family="Benign high-power event",
            description="Site master controller allocates additional capacity from an adjacent idle charger, ramping power from 60A to 125A.",
            duration_seconds=60.0,
            default_seed=403,
            components_involved=["grid_interface", "evse_controller", "power_converter"],
            scheduled_events=[
                SimulatedEventSchema(
                    event_id="EVT-BNG-03-A",
                    timestamp=5.0,
                    layer="cyber_protocol",
                    component_id="csms_backend",
                    event_type="START_TRANSACTION",
                    source="csms",
                    auth_status="authorized",
                    details={"requested_current": 60.0}
                ),
                SimulatedEventSchema(
                    event_id="EVT-BNG-03-B",
                    timestamp=22.0,
                    layer="grid",
                    component_id="grid_interface",
                    event_type="GRID_LIMIT_UPDATE",
                    source="grid_operator",
                    auth_status="authorized",
                    details={"allocated_limit": 125.0},
                    ground_truth=GroundTruthMetadata(is_malicious=False, target_signal="charging_current", expected_causal=True)
                )
            ],
            expected_physical_effects="Current steps to 125A; grid load increases to ~50 kW safely within transformer rating.",
            ground_truth_links=[],
            expected_outcome="Legitimate high power allocation; safe operation.",
            safety_limitations="Grid transformer impedance not modeled in detail."
        ),

        # ==========================================
        # FAMILY 5: DELAYED ATTACK
        # ==========================================
        ScenarioSchema(
            scenario_id="SCN-DLY-01",
            name="Time-Bomb Current Surge (+40s Latency)",
            family="Delayed attack",
            description="Malicious payload lies dormant during 35 seconds of normal charging, then triggers an unauthorized current spike to 150A.",
            duration_seconds=60.0,
            default_seed=501,
            components_involved=["evse_controller", "power_converter", "battery_pack"],
            scheduled_events=[
                SimulatedEventSchema(
                    event_id="EVT-DLY-01-A",
                    timestamp=5.0,
                    layer="cyber_protocol",
                    component_id="csms_backend",
                    event_type="START_TRANSACTION",
                    source="csms",
                    auth_status="authorized",
                    details={"requested_current": 70.0}
                ),
                SimulatedEventSchema(
                    event_id="EVT-DLY-01-B",
                    timestamp=40.0,
                    layer="controller",
                    component_id="evse_controller",
                    event_type="CHANGE_CURRENT_LIMIT",
                    source="internal_firmware",
                    auth_status="unauthorized",
                    details={"current_limit": 150.0, "timer_trigger": "dormant_delay"},
                    ground_truth=GroundTruthMetadata(
                        is_malicious=True,
                        target_signal="charging_current",
                        expected_delta="+80A",
                        expected_causal=True,
                        rationale="Timer payload wakes at t=40s and overrides current to 150A."
                    )
                )
            ],
            expected_physical_effects="Normal behavior until t=40s; sharp 150A spike triggers rapid temperature acceleration in final 20 seconds.",
            ground_truth_links=[
                GroundTruthLinkSchema(
                    event_id="EVT-DLY-01-B",
                    target_signal="charging_current",
                    is_causal=True,
                    expected_delay_min=0.5,
                    expected_delay_max=2.0,
                    rationale="Dormant trigger overrides current."
                )
            ],
            expected_outcome="Delayed onset proven; counterfactual run without t=40s event confirms baseline stability.",
            safety_limitations="Illustrative timer mechanism."
        ),

        ScenarioSchema(
            scenario_id="SCN-DLY-02",
            name="Delayed Cooling Throttling Attack",
            family="Delayed attack",
            description="Charger runs at 110A normally, then at t=35s attacker throttles cooling to 10% when pack heat has already accumulated.",
            duration_seconds=60.0,
            default_seed=502,
            components_involved=["cooling_system", "battery_pack"],
            scheduled_events=[
                SimulatedEventSchema(
                    event_id="EVT-DLY-02-A",
                    timestamp=4.0,
                    layer="cyber_protocol",
                    component_id="csms_backend",
                    event_type="START_TRANSACTION",
                    source="csms",
                    auth_status="authorized",
                    details={"requested_current": 110.0}
                ),
                SimulatedEventSchema(
                    event_id="EVT-DLY-02-B",
                    timestamp=35.0,
                    layer="controller",
                    component_id="cooling_system",
                    event_type="COOLING_OVERRIDE",
                    source="local_attacker",
                    auth_status="unauthorized",
                    details={"cooling_factor": 0.1},
                    ground_truth=GroundTruthMetadata(is_malicious=True, target_signal="battery_temperature", expected_causal=True)
                )
            ],
            expected_physical_effects="Temperature slope steepens sharply after t=35s, reaching 46°C warning threshold.",
            ground_truth_links=[
                GroundTruthLinkSchema(
                    event_id="EVT-DLY-02-B",
                    target_signal="battery_temperature",
                    is_causal=True,
                    expected_delay_min=3.0,
                    expected_delay_max=20.0,
                    rationale="Delayed cooling loss traps heat."
                )
            ],
            expected_outcome="Delayed thermal escalation captured by correlation engine.",
            safety_limitations="Cooling circuit thermal inertia modeled via single time constant."
        ),

        ScenarioSchema(
            scenario_id="SCN-DLY-03",
            name="Stealth Creep Current Escalation",
            family="Delayed attack",
            description="Attacker slowly increases current by 25A every 15 seconds to avoid threshold step-change alarms.",
            duration_seconds=60.0,
            default_seed=503,
            components_involved=["evse_controller", "power_converter", "battery_pack"],
            scheduled_events=[
                SimulatedEventSchema(
                    event_id="EVT-DLY-03-A",
                    timestamp=5.0,
                    layer="cyber_protocol",
                    component_id="csms_backend",
                    event_type="START_TRANSACTION",
                    source="csms",
                    auth_status="authorized",
                    details={"requested_current": 70.0}
                ),
                SimulatedEventSchema(
                    event_id="EVT-DLY-03-B",
                    timestamp=20.0,
                    layer="controller",
                    component_id="evse_controller",
                    event_type="CHANGE_CURRENT_LIMIT",
                    source="man_in_the_middle",
                    auth_status="unauthorized",
                    details={"current_limit": 105.0}
                ),
                SimulatedEventSchema(
                    event_id="EVT-DLY-03-C",
                    timestamp=35.0,
                    layer="controller",
                    component_id="evse_controller",
                    event_type="CHANGE_CURRENT_LIMIT",
                    source="man_in_the_middle",
                    auth_status="unauthorized",
                    details={"current_limit": 140.0},
                    ground_truth=GroundTruthMetadata(is_malicious=True, target_signal="battery_temperature", expected_causal=True)
                )
            ],
            expected_physical_effects="Staircase current increase (70A -> 105A -> 140A) with cumulative thermal heating.",
            ground_truth_links=[
                GroundTruthLinkSchema(
                    event_id="EVT-DLY-03-C",
                    target_signal="charging_current",
                    is_causal=True,
                    expected_delay_min=0.5,
                    expected_delay_max=2.0,
                    rationale="Second step pushes current into warning zone."
                )
            ],
            expected_outcome="Cumulative multi-step attack identified; counterfactual replay isolates incremental effect.",
            safety_limitations="Rate-of-change alarms absent in basic EVSE firmware."
        ),

        # ==========================================
        # FAMILY 6: MASKED ATTACK
        # ==========================================
        ScenarioSchema(
            scenario_id="SCN-MSK-01",
            name="Overcurrent Surge Masked by Frozen Temp Sensor",
            family="Masked attack",
            description="Attacker injects 150A overcurrent while simultaneously spoofing the temperature sensor to freeze at 25°C, blinding operators.",
            duration_seconds=60.0,
            default_seed=601,
            components_involved=["evse_controller", "temperature_sensor", "power_converter", "battery_pack"],
            scheduled_events=[
                SimulatedEventSchema(
                    event_id="EVT-MSK-01-A",
                    timestamp=4.0,
                    layer="cyber_protocol",
                    component_id="csms_backend",
                    event_type="START_TRANSACTION",
                    source="csms",
                    auth_status="authorized",
                    details={"requested_current": 60.0}
                ),
                SimulatedEventSchema(
                    event_id="EVT-MSK-01-B",
                    timestamp=15.0,
                    layer="controller",
                    component_id="evse_controller",
                    event_type="CHANGE_CURRENT_LIMIT",
                    source="local_attacker",
                    auth_status="unauthorized",
                    details={"current_limit": 150.0},
                    ground_truth=GroundTruthMetadata(is_malicious=True, target_signal="battery_temperature", expected_causal=True)
                ),
                SimulatedEventSchema(
                    event_id="EVT-MSK-01-C",
                    timestamp=15.0,
                    layer="sensor",
                    component_id="temperature_sensor",
                    event_type="SENSOR_INJECT_FAULT",
                    source="local_attacker",
                    auth_status="unauthorized",
                    details={"fault_type": "stuck", "parameter": 25.0},
                    ground_truth=GroundTruthMetadata(
                        is_malicious=True,
                        target_signal="sensor_temperature",
                        expected_delta="Masked at 25°C",
                        expected_causal=True,
                        rationale="Sensor reading frozen to disguise genuine battery heating."
                    )
                )
            ],
            expected_physical_effects="Actual battery temperature rises to ~48°C (crossing warning), while sensor temperature shows a deceptively flat 25.0°C.",
            ground_truth_links=[
                GroundTruthLinkSchema(
                    event_id="EVT-MSK-01-B",
                    target_signal="battery_temperature",
                    is_causal=True,
                    expected_delay_min=5.0,
                    expected_delay_max=30.0,
                    rationale="150A overcurrent causes physical heating."
                ),
                GroundTruthLinkSchema(
                    event_id="EVT-MSK-01-C",
                    target_signal="sensor_temperature",
                    is_causal=True,
                    expected_delay_min=0.0,
                    expected_delay_max=1.0,
                    rationale="Sensor clamp masks physical reality."
                )
            ],
            expected_outcome="CyberTrace AI unmasks discrepancy between power delivery model and frozen sensor telemetry.",
            safety_limitations="Independent thermal sensor redundancy not modeled."
        ),

        ScenarioSchema(
            scenario_id="SCN-MSK-02",
            name="Cooling Sabotage Concealed by Faked Status Reports",
            family="Masked attack",
            description="Cooling factor is cut to 0.0 while status notifications continue reporting 'Pumps Active / Status OK'.",
            duration_seconds=60.0,
            default_seed=602,
            components_involved=["cooling_system", "battery_pack", "csms_backend"],
            scheduled_events=[
                SimulatedEventSchema(
                    event_id="EVT-MSK-02-A",
                    timestamp=5.0,
                    layer="cyber_protocol",
                    component_id="csms_backend",
                    event_type="START_TRANSACTION",
                    source="csms",
                    auth_status="authorized",
                    details={"requested_current": 100.0}
                ),
                SimulatedEventSchema(
                    event_id="EVT-MSK-02-B",
                    timestamp=18.0,
                    layer="controller",
                    component_id="cooling_system",
                    event_type="COOLING_OVERRIDE",
                    source="man_in_the_middle",
                    auth_status="unauthorized",
                    details={"cooling_factor": 0.0},
                    ground_truth=GroundTruthMetadata(is_malicious=True, target_signal="battery_temperature", expected_causal=True)
                ),
                SimulatedEventSchema(
                    event_id="EVT-MSK-02-C",
                    timestamp=19.0,
                    layer="cyber_protocol",
                    component_id="csms_backend",
                    event_type="STATUS_NOTIFICATION",
                    source="man_in_the_middle",
                    auth_status="spoofed",
                    details={"status": "Cooling_Operational_Normal"},
                    ground_truth=GroundTruthMetadata(is_malicious=True)
                )
            ],
            expected_physical_effects="Temperature rises continuously past 45°C despite reassuring status messages.",
            ground_truth_links=[
                GroundTruthLinkSchema(
                    event_id="EVT-MSK-02-B",
                    target_signal="battery_temperature",
                    is_causal=True,
                    expected_delay_min=4.0,
                    expected_delay_max=25.0,
                    rationale="Physical cooling sabotage drives thermal buildup."
                )
            ],
            expected_outcome="Physical telemetry refutes cyber status messages; counterfactual confirms cooling cut impact.",
            safety_limitations="Simplified flow telemetry."
        ),

        ScenarioSchema(
            scenario_id="SCN-MSK-03",
            name="High Current Inversion with Suppressed Warning Flags",
            family="Masked attack",
            description="Attacker commands 145A and alters controller logging to omit warning alert dispatch.",
            duration_seconds=60.0,
            default_seed=603,
            components_involved=["evse_controller", "battery_pack"],
            scheduled_events=[
                SimulatedEventSchema(
                    event_id="EVT-MSK-03-A",
                    timestamp=4.0,
                    layer="cyber_protocol",
                    component_id="csms_backend",
                    event_type="START_TRANSACTION",
                    source="csms",
                    auth_status="authorized",
                    details={"requested_current": 65.0}
                ),
                SimulatedEventSchema(
                    event_id="EVT-MSK-03-B",
                    timestamp=16.0,
                    layer="controller",
                    component_id="evse_controller",
                    event_type="CHANGE_CURRENT_LIMIT",
                    source="local_attacker",
                    auth_status="unauthorized",
                    details={"current_limit": 145.0, "suppress_logs": True},
                    ground_truth=GroundTruthMetadata(is_malicious=True, target_signal="charging_current", expected_causal=True)
                )
            ],
            expected_physical_effects="Current elevates to 145A; battery temperature climbs to 46°C.",
            ground_truth_links=[
                GroundTruthLinkSchema(
                    event_id="EVT-MSK-03-B",
                    target_signal="charging_current",
                    is_causal=True,
                    expected_delay_min=0.5,
                    expected_delay_max=2.0,
                    rationale="Rogue current command executed directly."
                )
            ],
            expected_outcome="Physical telemetry reflects overcurrent despite silenced controller log events.",
            safety_limitations="Assumes controller logging layer is accessible."
        ),

        # ==========================================
        # FAMILY 7: FLEET ATTACK
        # ==========================================
        ScenarioSchema(
            scenario_id="SCN-FLT-05",
            name="Coordinated Multi-Charger Grid Spike (Fleet Sync)",
            family="Fleet attack",
            description="Simulated fleet-wide synchronized step command pulling 150A, testing substation feeder capacity and local grid transformer loading.",
            duration_seconds=60.0,
            default_seed=701,
            components_involved=["csms_backend", "evse_controller", "power_converter", "grid_interface"],
            scheduled_events=[
                SimulatedEventSchema(
                    event_id="EVT-FLT-05-A",
                    timestamp=5.0,
                    layer="cyber_protocol",
                    component_id="csms_backend",
                    event_type="START_TRANSACTION",
                    source="csms",
                    auth_status="authorized",
                    details={"requested_current": 70.0}
                ),
                SimulatedEventSchema(
                    event_id="EVT-FLT-05-B",
                    timestamp=20.0,
                    layer="cyber_protocol",
                    component_id="csms_backend",
                    event_type="CHANGE_CURRENT_LIMIT",
                    source="man_in_the_middle",
                    auth_status="unauthorized",
                    details={"current_limit": 150.0, "broadcast_fleet": True},
                    ground_truth=GroundTruthMetadata(
                        is_malicious=True,
                        target_signal="grid_load",
                        expected_delta="+32 kW single / 320 kW fleet",
                        expected_causal=True,
                        rationale="Synchronized current spike surges local grid transformer demand."
                    )
                )
            ],
            expected_physical_effects="Grid demand spikes from 28 kW to 60 kW on this node (representing severe cluster-wide load shock).",
            ground_truth_links=[
                GroundTruthLinkSchema(
                    event_id="EVT-FLT-05-B",
                    target_signal="grid_load",
                    is_causal=True,
                    expected_delay_min=0.5,
                    expected_delay_max=2.0,
                    rationale="Overcurrent drives proportional power draw from feeder."
                )
            ],
            expected_outcome="Identified as fleet-scale coordinated demand surge.",
            safety_limitations="Grid frequency and voltage sag dynamics are abstracted."
        ),

        ScenarioSchema(
            scenario_id="SCN-FLT-06",
            name="Fleet-Wide Cooling Valve Lockout",
            family="Fleet attack",
            description="Malicious management profile broadcast to all charging stalls commanding cooling valve lock to 0.1 efficiency.",
            duration_seconds=60.0,
            default_seed=702,
            components_involved=["cooling_system", "battery_pack"],
            scheduled_events=[
                SimulatedEventSchema(
                    event_id="EVT-FLT-06-A",
                    timestamp=4.0,
                    layer="cyber_protocol",
                    component_id="csms_backend",
                    event_type="START_TRANSACTION",
                    source="csms",
                    auth_status="authorized",
                    details={"requested_current": 90.0}
                ),
                SimulatedEventSchema(
                    event_id="EVT-FLT-06-B",
                    timestamp=15.0,
                    layer="controller",
                    component_id="cooling_system",
                    event_type="COOLING_OVERRIDE",
                    source="csms",
                    auth_status="unauthorized",
                    details={"cooling_factor": 0.1, "fleet_broadcast": True},
                    ground_truth=GroundTruthMetadata(is_malicious=True, target_signal="battery_temperature", expected_causal=True)
                )
            ],
            expected_physical_effects="Gradual heat trap across all stalls; temperature reaches 45°C by t=50s.",
            ground_truth_links=[
                GroundTruthLinkSchema(
                    event_id="EVT-FLT-06-B",
                    target_signal="battery_temperature",
                    is_causal=True,
                    expected_delay_min=5.0,
                    expected_delay_max=35.0,
                    rationale="Fleet cooling shutdown accumulates heat."
                )
            ],
            expected_outcome="Fleet vulnerability highlighted; replay proves cooling was decisive factor.",
            safety_limitations="Simulates single node within fleet."
        ),

        ScenarioSchema(
            scenario_id="SCN-FLT-07",
            name="Synchronized Cycling Resonance Attack",
            family="Fleet attack",
            description="Alternating 140A / 40A square wave current pulses every 10 seconds to stress thermal fatigue and grid voltage stability.",
            duration_seconds=60.0,
            default_seed=703,
            components_involved=["evse_controller", "power_converter", "battery_pack", "grid_interface"],
            scheduled_events=[
                SimulatedEventSchema(
                    event_id="EVT-FLT-07-A",
                    timestamp=5.0,
                    layer="cyber_protocol",
                    component_id="csms_backend",
                    event_type="START_TRANSACTION",
                    source="csms",
                    auth_status="authorized",
                    details={"requested_current": 60.0}
                ),
                SimulatedEventSchema(
                    event_id="EVT-FLT-07-B",
                    timestamp=15.0,
                    layer="controller",
                    component_id="evse_controller",
                    event_type="CHANGE_CURRENT_LIMIT",
                    source="man_in_the_middle",
                    auth_status="unauthorized",
                    details={"current_limit": 140.0}
                ),
                SimulatedEventSchema(
                    event_id="EVT-FLT-07-C",
                    timestamp=30.0,
                    layer="controller",
                    component_id="evse_controller",
                    event_type="CHANGE_CURRENT_LIMIT",
                    source="man_in_the_middle",
                    auth_status="unauthorized",
                    details={"current_limit": 40.0}
                ),
                SimulatedEventSchema(
                    event_id="EVT-FLT-07-D",
                    timestamp=45.0,
                    layer="controller",
                    component_id="evse_controller",
                    event_type="CHANGE_CURRENT_LIMIT",
                    source="man_in_the_middle",
                    auth_status="unauthorized",
                    details={"current_limit": 140.0},
                    ground_truth=GroundTruthMetadata(is_malicious=True, target_signal="charging_current", expected_causal=True)
                )
            ],
            expected_physical_effects="Sawtooth power oscillation causing mechanical and thermal expansion stress.",
            ground_truth_links=[],
            expected_outcome="Cyclic manipulation detected.",
            safety_limitations="Battery mechanical strain not calculated directly."
        ),

        # ==========================================
        # FAMILY 8: DEFENDED ATTACK
        # ==========================================
        ScenarioSchema(
            scenario_id="SCN-DEF-01",
            name="BMS Hardware Breaker Trips Rogue Overcurrent",
            family="Defended attack",
            description="Attacker bypasses EVSE controller and injects extreme 150A overcurrent with disabled cooling; battery heats up, and at 60°C the independent BMS hardware breaker successfully trips to FAULT.",
            duration_seconds=60.0,
            default_seed=801,
            components_involved=["evse_controller", "bms", "battery_pack", "cooling_system"],
            scheduled_events=[
                SimulatedEventSchema(
                    event_id="EVT-DEF-01-A",
                    timestamp=4.0,
                    layer="cyber_protocol",
                    component_id="csms_backend",
                    event_type="START_TRANSACTION",
                    source="csms",
                    auth_status="authorized",
                    details={"requested_current": 70.0}
                ),
                SimulatedEventSchema(
                    event_id="EVT-DEF-01-B",
                    timestamp=10.0,
                    layer="cyber_protocol",
                    component_id="evse_controller",
                    event_type="BMS_OVERRIDE_ATTEMPT",
                    source="local_attacker",
                    auth_status="unauthorized",
                    details={"current_limit": 150.0, "override_active": True},
                    ground_truth=GroundTruthMetadata(is_malicious=True, target_signal="charging_current", expected_causal=True)
                ),
                SimulatedEventSchema(
                    event_id="EVT-DEF-01-C",
                    timestamp=12.0,
                    layer="controller",
                    component_id="cooling_system",
                    event_type="COOLING_OVERRIDE",
                    source="local_attacker",
                    auth_status="unauthorized",
                    details={"cooling_factor": 0.0},
                    ground_truth=GroundTruthMetadata(is_malicious=True, target_signal="battery_temperature", expected_causal=True)
                )
            ],
            expected_physical_effects="Rapid heating until temperature reaches 60.0°C; BMS hardware safety breaker disconnects charging circuit, dropping current to 0A.",
            ground_truth_links=[
                GroundTruthLinkSchema(
                    event_id="EVT-DEF-01-B",
                    target_signal="charging_current",
                    is_causal=True,
                    expected_delay_min=0.5,
                    expected_delay_max=2.0,
                    rationale="Overcurrent initiated until hardware defense acts."
                )
            ],
            expected_outcome="Defended state demonstrated: BMS protection successfully isolates battery pack before catastrophic runaway occurs.",
            safety_limitations="Post-trip residual thermal inertia can still cause a minor temperature overshoot."
        ),

        ScenarioSchema(
            scenario_id="SCN-DEF-02",
            name="Secondary Thermal Cutoff Mitigates Runaway",
            family="Defended attack",
            description="Overcurrent injected at t=15s, but EVSE secondary safety monitor halts session at t=35s before reaching critical 60°C trip.",
            duration_seconds=60.0,
            default_seed=802,
            components_involved=["evse_controller", "power_converter", "battery_pack"],
            scheduled_events=[
                SimulatedEventSchema(
                    event_id="EVT-DEF-02-A",
                    timestamp=4.0,
                    layer="cyber_protocol",
                    component_id="csms_backend",
                    event_type="START_TRANSACTION",
                    source="csms",
                    auth_status="authorized",
                    details={"requested_current": 70.0}
                ),
                SimulatedEventSchema(
                    event_id="EVT-DEF-02-B",
                    timestamp=15.0,
                    layer="controller",
                    component_id="evse_controller",
                    event_type="CHANGE_CURRENT_LIMIT",
                    source="man_in_the_middle",
                    auth_status="unauthorized",
                    details={"current_limit": 145.0},
                    ground_truth=GroundTruthMetadata(is_malicious=True, target_signal="charging_current", expected_causal=True)
                ),
                SimulatedEventSchema(
                    event_id="EVT-DEF-02-C",
                    timestamp=35.0,
                    layer="controller",
                    component_id="evse_controller",
                    event_type="EMERGENCY_STOP",
                    source="operator",
                    auth_status="authorized",
                    details={"reason": "Secondary watchdog thermal trip"},
                    ground_truth=GroundTruthMetadata(
                        is_malicious=False,
                        target_signal="charging_current",
                        expected_delta="Cut to 0A",
                        expected_causal=True,
                        rationale="Watchdog terminates session, mitigating runaway."
                    )
                )
            ],
            expected_physical_effects="Temperature climbs towards 46°C, but emergency cutoff at t=35s prevents further heating, leveling temperature.",
            ground_truth_links=[
                GroundTruthLinkSchema(
                    event_id="EVT-DEF-02-C",
                    target_signal="charging_current",
                    is_causal=True,
                    expected_delay_min=0.5,
                    expected_delay_max=2.0,
                    rationale="Defensive watchdog stops power delivery."
                )
            ],
            expected_outcome="Defensive intervention successfully proven by comparing original vs without defensive trip.",
            safety_limitations="Requires functioning independent watchdog circuit."
        ),

        ScenarioSchema(
            scenario_id="SCN-DEF-03",
            name="Emergency Stop Interruption of Current Escalation",
            family="Defended attack",
            description="Physical emergency stop button activated on charger enclosure immediately halts escalating attack.",
            duration_seconds=60.0,
            default_seed=803,
            components_involved=["evse_controller", "power_converter", "battery_pack"],
            scheduled_events=[
                SimulatedEventSchema(
                    event_id="EVT-DEF-03-A",
                    timestamp=5.0,
                    layer="cyber_protocol",
                    component_id="csms_backend",
                    event_type="START_TRANSACTION",
                    source="csms",
                    auth_status="authorized",
                    details={"requested_current": 75.0}
                ),
                SimulatedEventSchema(
                    event_id="EVT-DEF-03-B",
                    timestamp=15.0,
                    layer="controller",
                    component_id="evse_controller",
                    event_type="CHANGE_CURRENT_LIMIT",
                    source="local_attacker",
                    auth_status="unauthorized",
                    details={"current_limit": 150.0}
                ),
                SimulatedEventSchema(
                    event_id="EVT-DEF-03-C",
                    timestamp=22.0,
                    layer="hardware",
                    component_id="evse_controller",
                    event_type="EMERGENCY_STOP",
                    source="operator",
                    auth_status="authorized",
                    details={"reason": "Attendant hit manual E-stop button"}
                )
            ],
            expected_physical_effects="Current quickly drops to 0A at t=22s; temperature peaks early at only 33°C.",
            ground_truth_links=[],
            expected_outcome="Manual defensive intervention prevents hazardous overheating.",
            safety_limitations="Human reaction time abstracted."
        ),

        ScenarioSchema(
            scenario_id="SCN-DEF-04",
            name="OCPP Anomaly Guard Rejects Malicious Profile",
            family="Defended attack",
            description="Firewall/Guard layer detects an unauthorized profile update and rejects it, keeping charger current at safe nominal 70A.",
            duration_seconds=60.0,
            default_seed=804,
            components_involved=["csms_backend", "evse_controller", "power_converter"],
            scheduled_events=[
                SimulatedEventSchema(
                    event_id="EVT-DEF-04-A",
                    timestamp=4.0,
                    layer="cyber_protocol",
                    component_id="csms_backend",
                    event_type="START_TRANSACTION",
                    source="csms",
                    auth_status="authorized",
                    details={"requested_current": 70.0}
                ),
                SimulatedEventSchema(
                    event_id="EVT-DEF-04-B",
                    timestamp=18.0,
                    layer="cyber_protocol",
                    component_id="evse_controller",
                    event_type="STATUS_NOTIFICATION",
                    source="operator",
                    auth_status="authorized",
                    details={"security_log": "Rejected unauthorized SetChargingProfile: missing digital signature"},
                    ground_truth=GroundTruthMetadata(is_malicious=False)
                )
            ],
            expected_physical_effects="Current stays rock-solid at 70A throughout; battery temperature stabilizes at 30°C.",
            ground_truth_links=[],
            expected_outcome="Protocol defense successfully neutralizes attempted attack before physical actuation.",
            safety_limitations="Requires public-key infrastructure (PKI) integration."
        ),

        # ==========================================
        # TIER 2: SENSOR FAULT INJECTION SCENARIOS (F11)
        # ==========================================
        ScenarioSchema(
            scenario_id="SCN-T2-FLT-01",
            name="Linear Thermistor Calibration Drift",
            family="Sensor fault",
            description="Thermistor analog circuit experiences continuous thermal calibration drift (+0.25°C/s) while physical cell temperature stays nominal at 31°C.",
            duration_seconds=60.0,
            default_seed=901,
            components_involved=["evse_controller", "battery_pack", "temperature_sensor"],
            scheduled_events=[
                SimulatedEventSchema(
                    event_id="EVT-T2-FLT-01-A",
                    timestamp=5.0,
                    layer="cyber_protocol",
                    component_id="csms_backend",
                    event_type="START_TRANSACTION",
                    source="csms",
                    auth_status="authorized",
                    details={"requested_current": 70.0}
                ),
                SimulatedEventSchema(
                    event_id="EVT-T2-FLT-01-B",
                    timestamp=15.0,
                    layer="physical_electrical",
                    component_id="temperature_sensor",
                    event_type="SENSOR_DRIFT",
                    source="internal_bms",
                    auth_status="authorized",
                    details={"drift_rate_c_per_sec": 0.25}
                )
            ],
            expected_physical_effects="Reported sensor temperature drifts upward to >42°C, producing a large physics residual while physical battery remains safe.",
            ground_truth_links=[],
            expected_outcome="Physics consistency checker flags sensor drift anomaly without interrupting physical charging.",
            safety_limitations="Simulation abstraction of thermistor degradation.",
            is_held_out=True
        ),

        ScenarioSchema(
            scenario_id="SCN-T2-FLT-02",
            name="Frozen ADC Sensor Stuck Reading",
            family="Sensor fault",
            description="BMS temperature sensor analog-to-digital converter freezes at 28.0°C during active 90A charging.",
            duration_seconds=60.0,
            default_seed=902,
            components_involved=["battery_pack", "temperature_sensor"],
            scheduled_events=[
                SimulatedEventSchema(
                    event_id="EVT-T2-FLT-02-A",
                    timestamp=5.0,
                    layer="cyber_protocol",
                    component_id="csms_backend",
                    event_type="START_TRANSACTION",
                    source="csms",
                    auth_status="authorized",
                    details={"requested_current": 90.0}
                ),
                SimulatedEventSchema(
                    event_id="EVT-T2-FLT-02-B",
                    timestamp=12.0,
                    layer="physical_electrical",
                    component_id="temperature_sensor",
                    event_type="SENSOR_STUCK",
                    source="internal_bms",
                    auth_status="authorized",
                    details={"stuck_value": 28.0}
                )
            ],
            expected_physical_effects="Reported temperature remains completely flat at 28°C despite continuous 90A current flow.",
            ground_truth_links=[],
            expected_outcome="Consistency checker flags stuck sensor reading and alerts investigator to ADC fault.",
            safety_limitations="Illustrative frozen register testbed.",
            is_held_out=True
        ),

        ScenarioSchema(
            scenario_id="SCN-T2-FLT-03",
            name="Isolated Transient Sensor Spike",
            family="Sensor fault",
            description="Electrical harness noise induces a single 1-second 85.0°C transient spike on the temperature channel.",
            duration_seconds=60.0,
            default_seed=903,
            components_involved=["temperature_sensor", "battery_pack"],
            scheduled_events=[
                SimulatedEventSchema(
                    event_id="EVT-T2-FLT-03-A",
                    timestamp=5.0,
                    layer="cyber_protocol",
                    component_id="csms_backend",
                    event_type="START_TRANSACTION",
                    source="csms",
                    auth_status="authorized",
                    details={"requested_current": 60.0}
                ),
                SimulatedEventSchema(
                    event_id="EVT-T2-FLT-03-B",
                    timestamp=22.0,
                    layer="physical_electrical",
                    component_id="temperature_sensor",
                    event_type="SENSOR_SPIKE",
                    source="internal_bms",
                    auth_status="authorized",
                    details={"spike_value": 85.0}
                )
            ],
            expected_physical_effects="Single-second impossible jump to 85°C, instantly returning to 29°C on subsequent second.",
            ground_truth_links=[],
            expected_outcome="Flagged as implausible instantaneous thermal jump violating thermal inertia.",
            safety_limitations="Simulated electromagnetic interference artifact.",
            is_held_out=True
        ),

        ScenarioSchema(
            scenario_id="SCN-T2-FLT-04",
            name="Temporary Sensor Lead Dropout",
            family="Sensor fault",
            description="Loose sensor connector causes signal dropout to 0.0°C between t=20s and t=28s.",
            duration_seconds=60.0,
            default_seed=904,
            components_involved=["temperature_sensor", "battery_pack"],
            scheduled_events=[
                SimulatedEventSchema(
                    event_id="EVT-T2-FLT-04-A",
                    timestamp=5.0,
                    layer="cyber_protocol",
                    component_id="csms_backend",
                    event_type="START_TRANSACTION",
                    source="csms",
                    auth_status="authorized",
                    details={"requested_current": 65.0}
                ),
                SimulatedEventSchema(
                    event_id="EVT-T2-FLT-04-B",
                    timestamp=20.0,
                    layer="physical_electrical",
                    component_id="temperature_sensor",
                    event_type="SENSOR_DROPOUT",
                    source="internal_bms",
                    auth_status="authorized",
                    details={"active": True}
                ),
                SimulatedEventSchema(
                    event_id="EVT-T2-FLT-04-C",
                    timestamp=28.0,
                    layer="physical_electrical",
                    component_id="temperature_sensor",
                    event_type="SENSOR_DROPOUT",
                    source="internal_bms",
                    auth_status="authorized",
                    details={"active": False}
                )
            ],
            expected_physical_effects="Sensor reading drops to 0.0°C for 8 seconds, then recovers to 30.5°C.",
            ground_truth_links=[],
            expected_outcome="Sensor quality marked as 'dropout', isolating wiring defect from physical battery state.",
            safety_limitations="Contact bounce and transient resistance abstracted.",
            is_held_out=True
        ),

        # ==========================================
        # TIER 2: CAN-STYLE SPOOFING SCENARIOS (F13)
        # ==========================================
        ScenarioSchema(
            scenario_id="SCN-T2-CAN-01",
            name="Powertrain CAN Current Command Injection",
            family="Attack",
            description="Compromised vehicle telematics unit injects unauthorized 140A fast-charge current requests over the internal CAN bus.",
            duration_seconds=60.0,
            default_seed=905,
            components_involved=["can_bus", "evse_controller", "battery_pack", "cooling_system"],
            scheduled_events=[
                SimulatedEventSchema(
                    event_id="EVT-T2-CAN-01-A",
                    timestamp=5.0,
                    layer="cyber_protocol",
                    component_id="csms_backend",
                    event_type="START_TRANSACTION",
                    source="csms",
                    auth_status="authorized",
                    details={"requested_current": 50.0}
                ),
                SimulatedEventSchema(
                    event_id="EVT-T2-CAN-01-B",
                    timestamp=18.0,
                    layer="cyber_protocol",
                    component_id="can_bus",
                    event_type="CAN_SPOOF_CURRENT",
                    source="in_vehicle_can",
                    auth_status="spoofed",
                    details={"requested_current": 140.0}
                )
            ],
            expected_physical_effects="Actual current surges to 140A; battery temperature accelerates past 60°C.",
            ground_truth_links=[],
            expected_outcome="Causal attribution traces temperature rise to spoofed CAN bus message with high confidence.",
            safety_limitations="Simulated CAN payload; no physical vehicle connection.",
            is_held_out=True
        ),

        ScenarioSchema(
            scenario_id="SCN-T2-CAN-02",
            name="CAN Thermal Telemetry Deception",
            family="Masked attack",
            description="Malicious CAN frames report artificially low 22°C pack temperatures to trick BMS into continuing excessive current delivery.",
            duration_seconds=60.0,
            default_seed=906,
            components_involved=["can_bus", "evse_controller", "battery_pack"],
            scheduled_events=[
                SimulatedEventSchema(
                    event_id="EVT-T2-CAN-02-A",
                    timestamp=5.0,
                    layer="cyber_protocol",
                    component_id="csms_backend",
                    event_type="START_TRANSACTION",
                    source="csms",
                    auth_status="authorized",
                    details={"requested_current": 135.0}
                ),
                SimulatedEventSchema(
                    event_id="EVT-T2-CAN-02-B",
                    timestamp=15.0,
                    layer="cyber_protocol",
                    component_id="can_bus",
                    event_type="CAN_SPOOF_TEMPERATURE",
                    source="in_vehicle_can",
                    auth_status="spoofed",
                    details={"spoofed_temperature": 22.0}
                )
            ],
            expected_physical_effects="CAN bus shows deceptive 22°C while actual physical cell temperature surpasses 64°C.",
            ground_truth_links=[],
            expected_outcome="Physics consistency observer detects divergence between reported CAN reading and physical Joule heating twin.",
            safety_limitations="Illustrative spoofing simulation.",
            is_held_out=True
        )
    ]

    return scenarios


SCENARIOS_MAP: Dict[str, ScenarioSchema] = {s.scenario_id: s for s in build_scenario_library()}

