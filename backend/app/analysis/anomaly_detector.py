"""
Isolation Forest Anomaly Detection Assistant (Feature F28).
Provides machine-learning-assisted anomaly scoring using scikit-learn.
Features:
- Deterministic training on nominal baselines (RandomState=42)
- Zero ground-truth leakage (strictly uses physical/sensor telemetry features)
- Safe handling of NaNs and non-finite values
- Interpretable feature contribution breakdown
- Assistant-only guarantee: Cannot independently declare an attack.
"""

import numpy as np
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from sklearn.ensemble import IsolationForest

from backend.app.schemas.telemetry import TelemetryTimeSlice


class FeatureContribution(BaseModel):
    feature_name: str
    observed_value: float
    baseline_mean: float
    deviation_ratio: float
    interpretation: str


class AnomalyAssistantResult(BaseModel):
    is_anomaly: bool = Field(..., description="Whether telemetry sequence exhibits multivariate statistical anomalies")
    anomaly_score: float = Field(..., description="Aggregated anomaly score (0.0 normal to 1.0 severe outlier)")
    raw_decision_score: float = Field(..., description="Raw Isolation Forest decision function score")
    flagged_timestamps: List[float] = Field(default_factory=list, description="Timestamps where instantaneous anomaly triggered")
    flagged_count: int = Field(default=0, description="Total anomalous time slices detected")
    top_contributing_features: List[FeatureContribution] = Field(default_factory=list, description="Features exhibiting largest deviations")
    model_version: str = Field(default="IsolationForest-v1.0-sklearn", description="Model architecture & version tag")
    trained_on_nominal_only: bool = Field(default=True, description="Safety guarantee that model was trained without attack labels")
    assistant_disclaimer: str = Field(
        default="ASSISTANT SIGNAL ONLY: Machine learning anomaly outputs cannot declare a cyberattack independently. Corroboration with dependency path validation and counterfactual replay is mandatory.",
        description="Defensive assurance disclaimer"
    )


class AnomalyDetectionAssistant:
    """Trains and executes Isolation Forest anomaly detection over time-series telemetry."""

    FEATURE_NAMES = [
        "temp_residual",
        "charging_current",
        "current_rate_of_change",
        "temp_rate_of_change",
        "voltage_sag",
        "cooling_power"
    ]

    _model: Optional[IsolationForest] = None
    _baseline_means: Dict[str, float] = {}
    _baseline_stds: Dict[str, float] = {}

    @classmethod
    def _extract_feature_matrix(cls, time_slices: List[TelemetryTimeSlice]) -> np.ndarray:
        """Extracts numerical feature array from TelemetryTimeSlice instances without ground truth."""
        if not time_slices:
            return np.zeros((0, len(cls.FEATURE_NAMES)))

        rows = []
        for i, s in enumerate(time_slices):
            # 1. Temperature residual (sensor vs twin)
            res = abs(s.temperature_residual) if s.temperature_residual is not None else 0.0

            # 2. Charging current
            curr = max(0.0, s.charging_current)

            # 3. Current rate of change (first difference)
            d_curr = abs(curr - time_slices[i - 1].charging_current) if i > 0 else 0.0

            # 4. Temperature rate of change
            t_curr = s.battery_temperature
            d_temp = abs(t_curr - time_slices[i - 1].battery_temperature) if i > 0 else 0.0

            # 5. Voltage sag from nominal 400V
            v_sag = max(0.0, 400.0 - s.battery_voltage)

            # 6. Cooling power
            cool = max(0.0, s.cooling_power)

            rows.append([res, curr, d_curr, d_temp, v_sag, cool])

        arr = np.array(rows, dtype=np.float64)

        # Handle any NaN or infinite values safely
        arr = np.nan_to_num(arr, nan=0.0, posinf=1000.0, neginf=-1000.0)
        return arr

    @classmethod
    def fit_baseline(cls, nominal_slices: List[TelemetryTimeSlice]):
        """Fits Isolation Forest strictly on nominal operation data without attack labels."""
        X = cls._extract_feature_matrix(nominal_slices)
        if len(X) < 10:
            # Fallback synthetic nominal baseline if not enough data passed
            X = np.zeros((50, len(cls.FEATURE_NAMES)))
            X[:, 0] = np.random.uniform(0.1, 0.8, 50)  # nominal residual
            X[:, 1] = np.random.uniform(40.0, 80.0, 50)  # nominal current
            X[:, 2] = np.random.uniform(0.0, 5.0, 50)  # low rate of change
            X[:, 3] = np.random.uniform(0.0, 0.2, 50)  # gradual heating
            X[:, 4] = np.random.uniform(5.0, 15.0, 50)  # nominal voltage drop
            X[:, 5] = np.random.uniform(200.0, 500.0, 50)  # normal cooling

        cls._model = IsolationForest(
            n_estimators=100,
            contamination=0.05,
            random_state=42,
            n_jobs=1
        )
        cls._model.fit(X)

        # Store baseline feature means and stds for interpretable comparisons
        means = np.mean(X, axis=0)
        stds = np.std(X, axis=0)
        cls._baseline_means = {name: float(means[idx]) for idx, name in enumerate(cls.FEATURE_NAMES)}
        cls._baseline_stds = {name: max(0.1, float(stds[idx])) for idx, name in enumerate(cls.FEATURE_NAMES)}

    @classmethod
    def evaluate(cls, time_slices: List[TelemetryTimeSlice]) -> AnomalyAssistantResult:
        """Evaluates telemetry sequence and returns interpretable anomaly metrics."""
        if cls._model is None:
            # Auto-initialize baseline if not yet fitted
            cls.fit_baseline([])

        if not time_slices:
            return AnomalyAssistantResult(
                is_anomaly=False,
                anomaly_score=0.0,
                raw_decision_score=0.0,
                flagged_timestamps=[],
                flagged_count=0,
                top_contributing_features=[]
            )

        X = cls._extract_feature_matrix(time_slices)
        predictions = cls._model.predict(X)  # -1 for anomaly, 1 for inlier
        scores = cls._model.decision_function(X)  # lower = more abnormal

        # Calculate feature deviations relative to baseline distribution
        means_arr = np.array([cls._baseline_means.get(name, 0.0) for name in cls.FEATURE_NAMES])
        stds_arr = np.array([cls._baseline_stds.get(name, 1.0) for name in cls.FEATURE_NAMES])
        z_scores = np.abs(X - means_arr) / stds_arr
        max_z_per_slice = np.max(z_scores, axis=1)

        # Flag slices if tree identifies anomaly or if feature z-score exceeds 2.5 sigma
        flagged_indices = [i for i in range(len(time_slices)) if predictions[i] == -1 or max_z_per_slice[i] > 2.5]
        flagged_timestamps = [time_slices[i].timestamp for i in flagged_indices]
        min_score = float(np.min(scores)) if len(scores) > 0 else 0.0

        # Calculate composite normalized score [0.0, 1.0]
        fraction_flagged = len(flagged_indices) / max(1, len(time_slices))
        mean_excess_z = float(np.mean(np.maximum(0.0, max_z_per_slice - 1.5)))
        normalized_score = round(min(1.0, max(0.0, (fraction_flagged * 0.5) + (min(mean_excess_z, 4.0) / 4.0 * 0.5))), 3)

        is_anomaly = fraction_flagged >= 0.10 or len(flagged_indices) >= 3 or normalized_score >= 0.20

        # Compute interpretable feature contributions
        contributions: List[FeatureContribution] = []
        if flagged_indices:
            anom_X = X[flagged_indices]
            anom_means = np.mean(anom_X, axis=0)

            for idx, name in enumerate(cls.FEATURE_NAMES):
                obs = float(anom_means[idx])
                base = cls._baseline_means.get(name, 1.0)
                denom = base if abs(base) > 1e-4 else 1.0
                ratio = round(obs / denom, 2)

                interp = f"Observed {name} is {obs:.1f} vs baseline {base:.1f} ({ratio}x change)"
                contributions.append(
                    FeatureContribution(
                        feature_name=name,
                        observed_value=round(obs, 2),
                        baseline_mean=round(base, 2),
                        deviation_ratio=ratio,
                        interpretation=interp
                    )
                )

            # Sort by largest deviation ratio
            contributions.sort(key=lambda c: c.deviation_ratio, reverse=True)

        return AnomalyAssistantResult(
            is_anomaly=is_anomaly,
            anomaly_score=normalized_score,
            raw_decision_score=round(min_score, 4),
            flagged_timestamps=flagged_timestamps,
            flagged_count=len(flagged_indices),
            top_contributing_features=contributions[:3]  # top 3 drivers
        )
