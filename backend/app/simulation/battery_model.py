"""
Battery and BMS Model (Feature F07).
Simulates State of Charge (SoC), Open Circuit Voltage, terminal voltage with IR drop,
and dynamic BMS protection thresholds.
"""

import math
from typing import Tuple, Dict, Any


class BatteryBMSModel:
    def __init__(
        self,
        capacity_kwh: float = 60.0,
        nominal_voltage: float = 400.0,
        internal_resistance_ohm: float = 0.025,
        initial_soc: float = 30.0,
        max_voltage_v: float = 450.0,
        min_voltage_v: float = 300.0
    ):
        self.capacity_kwh = capacity_kwh
        self.nominal_voltage = nominal_voltage
        self.internal_resistance_ohm = internal_resistance_ohm
        self.soc = max(0.0, min(100.0, initial_soc))  # %
        self.max_voltage_v = max_voltage_v
        self.min_voltage_v = min_voltage_v

        # Total capacity in Ampere-hours: (kWh * 1000) / V_nom
        self.capacity_ah = (capacity_kwh * 1000.0) / nominal_voltage
        self.coulombic_efficiency = 0.98

    def calculate_ocv(self, soc_percent: float) -> float:
        """
        Open-Circuit Voltage curve as function of SoC (400V nominal pack).
        V_ocv = 350.0 + 70.0 * (SoC / 100) + 4.0 * sin(pi * SoC / 100)
        """
        soc_norm = max(0.0, min(1.0, soc_percent / 100.0))
        return 350.0 + 70.0 * soc_norm + 4.0 * math.sin(math.pi * soc_norm)

    def compute_bms_recommended_limit(self, battery_temp_c: float) -> float:
        """
        BMS dynamic current recommendation based on SoC and pack temperature.
        - High SoC (>80%): taper current to prevent lithium plating.
        - High Temp (>45°C): throttle current to reduce Joule heating.
        """
        base_limit = 150.0

        # SoC taper
        if self.soc > 80.0:
            taper_factor = max(0.15, (100.0 - self.soc) / 20.0)
            base_limit *= taper_factor

        # Thermal throttling
        if battery_temp_c >= 55.0:
            base_limit = min(base_limit, 20.0)
        elif battery_temp_c >= 45.0:
            base_limit = min(base_limit, 50.0)

        return max(5.0, base_limit)

    def step(self, current_a: float, dt_seconds: float) -> Tuple[float, float, Dict[str, Any]]:
        """
        Integrates charging current for dt_seconds.
        Returns:
            (terminal_voltage_v, updated_soc_percent, status_flags)
        """
        # Integrate charge: Delta Q = I * dt * eta / 3600 (in Ah)
        delta_ah = (current_a * dt_seconds * self.coulombic_efficiency) / 3600.0
        delta_soc = (delta_ah / self.capacity_ah) * 100.0

        self.soc = max(0.0, min(100.0, self.soc + delta_soc))

        # Terminal voltage = V_ocv + I * R_int
        v_ocv = self.calculate_ocv(self.soc)
        v_terminal = v_ocv + (current_a * self.internal_resistance_ohm)
        v_terminal = max(self.min_voltage_v, min(self.max_voltage_v + 20.0, v_terminal))

        # Check BMS electrical limits
        overvoltage = v_terminal >= self.max_voltage_v
        full_charge = self.soc >= 100.0

        flags = {
            "overvoltage": overvoltage,
            "full_charge": full_charge,
            "v_ocv": v_ocv,
            "delta_soc": delta_soc
        }
        return v_terminal, self.soc, flags
