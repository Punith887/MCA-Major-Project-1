from datetime import datetime, timedelta, timezone

import pytest

from ai_engine.anomaly_detector import (
    InsufficientMetricsError,
    MetricObservation,
    detect_anomalies,
)


def make_observations(count: int) -> list[MetricObservation]:
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    return [
        MetricObservation(
            timestamp=start + timedelta(minutes=index),
            features={
                "cpu_cores": 0.05 + (index % 7) * 0.002,
                "memory_bytes": 100_000_000 + (index % 5) * 100_000,
                "request_rate": 1.0 + (index % 3) * 0.05,
                "error_rate": 0.0,
            },
        )
        for index in range(count)
    ]


def test_isolation_forest_flags_extreme_observation():
    observations = make_observations(80)
    observations[-1] = MetricObservation(
        timestamp=observations[-1].timestamp,
        features={
            "cpu_cores": 8.0,
            "memory_bytes": 8_000_000_000,
            "request_rate": 80.0,
            "error_rate": 12.0,
        },
    )

    scores = detect_anomalies(
        observations,
        minimum_samples=30,
        contamination=0.05,
    )

    assert len(scores) == len(observations)
    assert scores[-1].is_anomaly
    assert scores[-1].anomaly_score > 0


def test_detector_reports_insufficient_valid_samples():
    observations = make_observations(5)

    with pytest.raises(InsufficientMetricsError, match="At least 10"):
        detect_anomalies(
            observations,
            minimum_samples=10,
            contamination=0.05,
        )


def test_detector_omits_non_finite_samples():
    observations = make_observations(40)
    observations[0] = MetricObservation(
        timestamp=observations[0].timestamp,
        features={
            "cpu_cores": float("nan"),
            "memory_bytes": 1,
            "request_rate": 1,
            "error_rate": 0,
        },
    )

    scores = detect_anomalies(
        observations,
        minimum_samples=30,
        contamination=0.05,
    )

    assert len(scores) == 39
    assert all(score.timestamp != observations[0].timestamp for score in scores)


def test_detector_rejects_invalid_contamination():
    with pytest.raises(ValueError, match="contamination"):
        detect_anomalies(
            make_observations(30),
            minimum_samples=10,
            contamination=0.5,
        )
