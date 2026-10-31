from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest

FEATURE_NAMES = ("cpu_cores", "memory_bytes", "request_rate", "error_rate")


class InsufficientMetricsError(ValueError):
    """Raised when too few valid observations exist to fit the detector."""


@dataclass(frozen=True)
class MetricObservation:
    timestamp: datetime
    features: dict[str, float]


@dataclass(frozen=True)
class ScoredObservation:
    timestamp: datetime
    features: dict[str, float]
    anomaly_score: float
    is_anomaly: bool


def detect_anomalies(
    observations: Sequence[MetricObservation],
    *,
    minimum_samples: int,
    contamination: float,
) -> list[ScoredObservation]:
    """Score observed samples with Isolation Forest; scores are not probabilities."""
    if not 0 < contamination < 0.5:
        raise ValueError("contamination must be greater than 0 and less than 0.5")

    frame = pd.DataFrame(
        [observation.features for observation in observations],
        columns=FEATURE_NAMES,
    ).astype("float64")
    matrix = frame.to_numpy(dtype=np.float64)
    valid_rows = np.isfinite(matrix).all(axis=1)
    valid_indexes = np.flatnonzero(valid_rows)

    if len(valid_indexes) < minimum_samples:
        raise InsufficientMetricsError(
            f"At least {minimum_samples} valid metric samples are required; "
            f"received {len(valid_indexes)}."
        )

    valid_matrix = matrix[valid_rows]
    detector = IsolationForest(
        contamination=contamination,
        random_state=42,
        n_estimators=100,
        n_jobs=1,
    )
    labels = detector.fit_predict(valid_matrix)
    scores = -detector.decision_function(valid_matrix)

    return [
        ScoredObservation(
            timestamp=observations[index].timestamp,
            features={
                name: float(value)
                for name, value in zip(FEATURE_NAMES, valid_matrix[position], strict=True)
            },
            anomaly_score=float(scores[position]),
            is_anomaly=bool(labels[position] == -1),
        )
        for position, index in enumerate(valid_indexes)
    ]
