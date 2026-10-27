"""
Safe-by-Design Guard (Feature F15).
Enforces strict input validation, whitelists allowed simulation event types,
components, sources, and parameters. Rejects any arbitrary commands or payloads.
"""

from typing import Any, Dict, List, Optional
from enum import Enum


class AllowedEventType(str, Enum):
    START_TRANSACTION = "START_TRANSACTION"
    STOP_TRANSACTION = "STOP_TRANSACTION"
    SET_CHARGING_PROFILE = "SET_CHARGING_PROFILE"
    CHANGE_CURRENT_LIMIT = "CHANGE_CURRENT_LIMIT"
    FIRMWARE_UPDATE = "FIRMWARE_UPDATE"
    COOLING_OVERRIDE = "COOLING_OVERRIDE"
    STATUS_NOTIFICATION = "STATUS_NOTIFICATION"
    METER_VALUES = "METER_VALUES"
    BMS_OVERRIDE_ATTEMPT = "BMS_OVERRIDE_ATTEMPT"
    SENSOR_INJECT_FAULT = "SENSOR_INJECT_FAULT"
    EMERGENCY_STOP = "EMERGENCY_STOP"
    GRID_LIMIT_UPDATE = "GRID_LIMIT_UPDATE"
    CAN_SPOOF_TEMPERATURE = "CAN_SPOOF_TEMPERATURE"
    CAN_SPOOF_CURRENT = "CAN_SPOOF_CURRENT"
    DISABLE_COOLING = "DISABLE_COOLING"
    SENSOR_DRIFT = "SENSOR_DRIFT"
    SENSOR_STUCK = "SENSOR_STUCK"
    SENSOR_SPIKE = "SENSOR_SPIKE"
    SENSOR_DROPOUT = "SENSOR_DROPOUT"


class AllowedComponent(str, Enum):
    CSMS_BACKEND = "csms_backend"
    EVSE_CONTROLLER = "evse_controller"
    POWER_CONVERTER = "power_converter"
    BMS = "bms"
    BATTERY_PACK = "battery_pack"
    COOLING_SYSTEM = "cooling_system"
    TEMPERATURE_SENSOR = "temperature_sensor"
    CURRENT_SENSOR = "current_sensor"
    GRID_INTERFACE = "grid_interface"
    CAN_BUS = "can_bus"


class AllowedLayer(str, Enum):
    CYBER_PROTOCOL = "cyber_protocol"
    CONTROLLER = "controller"
    HARDWARE = "hardware"
    SENSOR = "sensor"
    GRID = "grid"
    CAN_BUS = "can_bus"
    PHYSICAL_ELECTRICAL = "physical_electrical"


class AllowedSource(str, Enum):
    CSMS = "csms"
    OPERATOR = "operator"
    LOCAL_ATTACKER = "local_attacker"
    MAN_IN_THE_MIDDLE = "man_in_the_middle"
    INTERNAL_FIRMWARE = "internal_firmware"
    DIAGNOSTIC_TOOL = "diagnostic_tool"
    SENSOR_HARDWARE = "sensor_hardware"
    BMS_HARDWARE = "bms_hardware"
    GRID_OPERATOR = "grid_operator"
    IN_VEHICLE_CAN = "in_vehicle_can"
    INTERNAL_BMS = "internal_bms"
    OCPP_CSMS = "ocpp_csms"


class AllowedAuthStatus(str, Enum):
    AUTHORIZED = "authorized"
    UNAUTHORIZED = "unauthorized"
    SPOOFED = "spoofed"
    BYPASSED = "bypassed"


class SafeByDesignGuard:
    """Validates inputs against strict whitelists to ensure safe simulated execution."""

    ALLOWED_EVENT_TYPES = {e.value for e in AllowedEventType}
    ALLOWED_COMPONENTS = {c.value for c in AllowedComponent}
    ALLOWED_LAYERS = {l.value for l in AllowedLayer}
    ALLOWED_SOURCES = {s.value for s in AllowedSource}
    ALLOWED_AUTH_STATUSES = {a.value for a in AllowedAuthStatus}

    FORBIDDEN_KEYWORDS = [
        "exec", "eval", "os.", "subprocess", "import", "open(", "system(",
        "/bin", "sh", "bash", "powershell", "cmd.exe", "DROP TABLE", "--"
    ]

    @classmethod
    def validate_event(cls, event_data: Dict[str, Any]) -> None:
        """Validates a single simulated event."""
        event_type = event_data.get("event_type")
        if event_type not in cls.ALLOWED_EVENT_TYPES:
            raise ValueError(f"Security Guard: Unauthorized event type '{event_type}'. Must be one of {sorted(cls.ALLOWED_EVENT_TYPES)}")

        comp = event_data.get("component_id")
        if comp not in cls.ALLOWED_COMPONENTS:
            raise ValueError(f"Security Guard: Unknown component '{comp}'. Must be one of {sorted(cls.ALLOWED_COMPONENTS)}")

        layer = event_data.get("layer")
        if layer and layer not in cls.ALLOWED_LAYERS:
            raise ValueError(f"Security Guard: Unknown layer '{layer}'. Must be one of {sorted(cls.ALLOWED_LAYERS)}")

        source = event_data.get("source")
        if source and source not in cls.ALLOWED_SOURCES:
            raise ValueError(f"Security Guard: Unknown source '{source}'. Must be one of {sorted(cls.ALLOWED_SOURCES)}")

        auth = event_data.get("auth_status")
        if auth and auth not in cls.ALLOWED_AUTH_STATUSES:
            raise ValueError(f"Security Guard: Unknown auth status '{auth}'. Must be one of {sorted(cls.ALLOWED_AUTH_STATUSES)}")

        # Check details for dangerous payload strings
        details = event_data.get("details", {})
        if isinstance(details, dict):
            for k, v in details.items():
                if isinstance(v, str):
                    for forbidden in cls.FORBIDDEN_KEYWORDS:
                        if forbidden in v.lower():
                            raise ValueError(f"Security Guard: Potentially unsafe string detected in detail '{k}'. Real exploits not permitted.")

    @classmethod
    def validate_simulation_parameters(cls, seed: int, duration: float) -> None:
        """Validates simulation execution bounds."""
        if not isinstance(seed, int) or seed < 0 or seed > 2_147_483_647:
            raise ValueError("Seed must be a non-negative 32-bit integer.")
        if duration <= 0 or duration > 600:
            raise ValueError("Duration must be between 1 and 600 seconds for simulation.")
