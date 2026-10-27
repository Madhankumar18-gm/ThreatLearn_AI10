"""
Thermal Model with Cooling & Advanced Sensor Faults (Features F08, F11, F13).
Models battery temperature dynamics using lumped thermal capacity, Joule heating (I^2 * R),
convective cooling dissipation, and advanced sensor-level fault distortions:
- Continuous linear temperature drift
- Stuck reading
- Isolated measurement spike
- Temporary sensor dropout / disconnection
- CAN-bus in-vehicle spoofed readings
"""

from typing import Dict, Any, Tuple, Optional


class ThermalModel:
    def __init__(
        self,
        c_thermal_j_k: float = 2400.0,
        r_thermal_k_w: float = 0.05,
        ambient_temp_c: float = 25.0,
        initial_temp_c: float = 25.0,
        warning_temp_c: float = 45.0,
        critical_temp_c: float = 60.0
    ):
        self.c_thermal = c_thermal_j_k
        self.r_thermal = r_thermal_k_w
        self.ambient_temp_c = ambient_temp_c
        self.temperature_c = initial_temp_c  # True physical state
        self.warning_temp_c = warning_temp_c
        self.critical_temp_c = critical_temp_c

        # Cooling efficiency multiplier: 1.0 = normal, 0.0 = total valve failure
        self.cooling_factor = 1.0

        # Tier 2 Advanced Sensor Fault States (Feature F11)
        self.sensor_stuck_val: Optional[float] = None
        self.sensor_offset = 0.0
        self.sensor_drift_rate = 0.0  # °C per second
        self.sensor_spike_val: Optional[float] = None
        self.sensor_dropout_active = False
        self.sensor_noise_sigma = 0.05
        self.elapsed_time = 0.0

        # Tier 2 CAN Spoof States (Feature F13)
        self.can_spoofed_temp: Optional[float] = None

    def set_cooling_degradation(self, factor: float) -> None:
        """Simulates cooling system throttling, pump failure, or valve blockage."""
        self.cooling_factor = max(0.0, factor)

    def inject_sensor_fault(self, fault_type: str, parameter: float = 0.0) -> None:
        """
        Simulates controlled sensor-level faults:
        - 'drift': linear temperature drift by parameter (°C/s)
        - 'stuck': sensor freezes at specified parameter or current value
        - 'spike': isolated measurement spike
        - 'dropout': sensor disconnects / reports zero or NaN
        - 'offset': adds static temperature bias
        - 'noise': elevates sensor noise standard deviation
        - 'can_spoof': sets a simulated in-vehicle CAN spoof reading
        - 'clear': resets all sensor faults
        """
        f = fault_type.lower()
        if f == "drift":
            self.sensor_drift_rate = parameter if parameter != 0 else 0.25
        elif f == "stuck":
            self.sensor_stuck_val = parameter if parameter > 0 else self.temperature_c
        elif f == "spike":
            self.sensor_spike_val = parameter if parameter > 0 else (self.temperature_c + 20.0)
        elif f == "dropout":
            self.sensor_dropout_active = (parameter > 0.5) if parameter is not None else True
        elif f == "offset":
            self.sensor_offset = parameter
        elif f == "noise":
            self.sensor_noise_sigma = parameter
        elif f == "can_spoof":
            self.can_spoofed_temp = parameter
        elif f == "clear":
            self.sensor_stuck_val = None
            self.sensor_offset = 0.0
            self.sensor_drift_rate = 0.0
            self.sensor_spike_val = None
            self.sensor_dropout_active = False
            self.sensor_noise_sigma = 0.05
            self.can_spoofed_temp = None

    def step(
        self,
        current_a: float,
        resistance_ohm: float,
        dt_seconds: float,
        rng_noise: float = 0.0
    ) -> Tuple[float, float, str, Dict[str, Any]]:
        """
        Integrates physical thermal state forward by dt_seconds, then derives reported sensor measurement.
        Distinguishes physical model state from sensor reported measurement.
        Returns: (actual_physical_temp, reported_sensor_temp, sensor_quality, metrics)
        """
        self.elapsed_time += dt_seconds

        # 1. Physical Model: Joule heating power (Watts)
        p_heat = (current_a ** 2) * resistance_ohm

        # 2. Cooling heat dissipation rate (Watts)
        delta_t_ambient = self.temperature_c - self.ambient_temp_c
        p_cool = (delta_t_ambient / self.r_thermal) * self.cooling_factor

        # 3. Net thermal power
        net_power = p_heat - p_cool
        delta_temp = (net_power / self.c_thermal) * dt_seconds
        self.temperature_c += delta_temp

        # Bound physical temperature to model limits (ambient to 150°C)
        self.temperature_c = max(self.ambient_temp_c, min(150.0, self.temperature_c))

        # 4. Derive Sensor-Reported Measurement (Feature F11 & F13)
        sensor_quality = "good"

        if self.sensor_dropout_active:
            reported_temp = 0.0  # Dropout reading
            sensor_quality = "dropout"
        elif self.sensor_spike_val is not None:
            reported_temp = self.sensor_spike_val
            sensor_quality = "fault"
            self.sensor_spike_val = None  # Single-step isolated spike
        elif self.sensor_stuck_val is not None:
            reported_temp = self.sensor_stuck_val
            sensor_quality = "fault"
        elif self.sensor_drift_rate != 0.0:
            drift = self.sensor_drift_rate * self.elapsed_time
            reported_temp = self.temperature_c + drift + (rng_noise * self.sensor_noise_sigma)
            sensor_quality = "suspect" if abs(drift) > 3.0 else "good"
        else:
            reported_temp = self.temperature_c + self.sensor_offset + (rng_noise * self.sensor_noise_sigma)
            if abs(self.sensor_offset) > 3.0 or self.sensor_noise_sigma > 1.0:
                sensor_quality = "suspect"

        metrics = {
            "p_heat_w": p_heat,
            "p_cool_w": p_cool,
            "net_power_w": net_power,
            "cooling_factor": self.cooling_factor,
            "can_spoofed_temp": self.can_spoofed_temp,
            "sensor_quality": sensor_quality
        }

        return self.temperature_c, reported_temp, metrics
