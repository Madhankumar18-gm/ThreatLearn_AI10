"""
Grid Feeder Digital Twin (Feature F09).
Provides a simplified distribution feeder model calculating aggregate demand,
feeder loading ratio, voltage sag response, and load threshold warnings.

NOTE: This is an illustrative simulation model for cyber-physical security analysis,
not an engineering-grade power-flow solver (e.g. OpenDSS or MATPOWER).
"""

from typing import Dict, Any, Tuple
from backend.app.schemas.fleet import FeederConfig


class GridFeederModel:
    """
    Simulates a distribution feeder supplying power to an EV charging depot or plaza.
    Tracks aggregate active power, loading percentage, and voltage sag response.
    """

    def __init__(self, config: FeederConfig = None):
        self.config = config or FeederConfig()

    def evaluate_step(self, total_power_kw: float, total_current_a: float) -> Dict[str, Any]:
        """
        Calculates feeder loading and estimated voltage sag for a given time step.

        Total Power = sum of individual charger active power demands (kW).
        Feeder Loading = Total Power / Configured Feeder Capacity.
        Voltage Response = V_nominal * max(0.70, 1.0 - alpha * rho - beta * rho^2).
        """
        # Ensure non-negative inputs
        power_kw = max(0.0, float(total_power_kw))
        current_a = max(0.0, float(total_current_a))

        # Feeder loading ratio (dimensionless) and percentage (%)
        capacity_kw = max(10.0, self.config.capacity_kw)
        loading_ratio = power_kw / capacity_kw
        loading_pct = loading_ratio * 100.0

        # Voltage response function
        alpha = self.config.voltage_sag_alpha
        beta = self.config.voltage_sag_beta
        nominal_v = self.config.nominal_voltage_v

        # Sag fraction with physical floor (e.g. 70% nominal minimum before protective brownout)
        sag_factor = max(0.70, 1.0 - (alpha * loading_ratio) - (beta * (loading_ratio ** 2)))
        estimated_voltage_v = round(nominal_v * sag_factor, 2)

        # Status determination
        if loading_pct >= self.config.critical_threshold_pct:
            status = "CRITICAL_OVERLOAD"
        elif loading_pct >= self.config.warning_threshold_pct:
            status = "WARNING"
        else:
            status = "NORMAL"

        return {
            "feeder_id": self.config.feeder_id,
            "feeder_name": self.config.feeder_name,
            "capacity_kw": capacity_kw,
            "total_power_kw": round(power_kw, 2),
            "total_current_a": round(current_a, 2),
            "loading_ratio": round(loading_ratio, 4),
            "feeder_loading_pct": round(loading_pct, 2),
            "feeder_voltage_v": estimated_voltage_v,
            "nominal_voltage_v": nominal_v,
            "voltage_sag_pct": round((1.0 - (estimated_voltage_v / nominal_v)) * 100.0, 2),
            "feeder_status": status,
            "is_overloaded": loading_pct >= self.config.warning_threshold_pct,
            "is_critical": loading_pct >= self.config.critical_threshold_pct,
            "is_simplified_simulation": True,
            "disclaimer": "Illustrative simplified cyber-physical model, not certified engineering power-flow analysis."
        }
