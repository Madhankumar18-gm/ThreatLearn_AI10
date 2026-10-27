"""
Core configuration and simulation physical model parameters.
All parameters represent illustrative engineering values for an EV Fast Charging Station (400V DC Fast Charger).
"""

from pydantic import BaseModel
import os
from pathlib import Path


class Settings(BaseModel):
    APP_NAME: str = "ThreatLens"
    APP_VERSION: str = "1.0.0 (Tier 1 Prototype)"
    TAGLINE: str = "See the Threat. Trace the Impact. Prove the Difference."
    DEBUG: bool = True
    SIMULATION_MODE_ENABLED: bool = True

    # Database settings
    DB_PATH: str = os.getenv("CYBERTRACE_DB_PATH", str(Path(__file__).resolve().parent.parent.parent / "cybertrace.db"))
    DATABASE_URL: str = f"sqlite:///{DB_PATH}"

    # Default Battery & Charger Physical Parameters
    BATTERY_CAPACITY_KWH: float = 60.0  # 60 kWh pack (approx 150 Ah at 400V)
    BATTERY_NOMINAL_VOLTAGE: float = 400.0  # Volts
    BATTERY_INTERNAL_RESISTANCE: float = 0.035  # Ohms (R_batt)
    BATTERY_INITIAL_SOC: float = 30.0  # 30% initial state of charge

    # Thermal Model Parameters
    # Simplified lumped capacitance thermal equation:
    # C_thermal * dT/dt = I^2 * R_batt - (T - T_ambient) / R_thermal
    THERMAL_HEAT_CAPACITY: float = 2400.0  # J/K (calibrated cell module thermal mass)
    THERMAL_RESISTANCE_AMBIENT: float = 0.05  # K/W (cooling interface thermal resistance)
    AMBIENT_TEMPERATURE: float = 25.0  # °C

    # Thresholds
    TEMP_WARNING_THRESHOLD: float = 45.0  # °C (BMS throttles/alerts)
    TEMP_CRITICAL_THRESHOLD: float = 60.0  # °C (BMS safety trip / emergency cutoff)
    CURRENT_WARNING_THRESHOLD: float = 120.0  # Amperes
    CURRENT_CRITICAL_THRESHOLD: float = 160.0  # Amperes
    VOLTAGE_MAX_LIMIT: float = 450.0  # Volts

    # Charger Hardware Limits
    CHARGER_HARDWARE_MAX_CURRENT: float = 150.0  # Amperes nominal fast charger limit
    CHARGER_DEFAULT_REQUESTED_CURRENT: float = 80.0  # Amperes


settings = Settings()
