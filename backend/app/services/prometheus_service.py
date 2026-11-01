from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
import math
import time

import httpx

from ai_engine.anomaly_detector import MetricObservation


class PrometheusError(RuntimeError):
    """Raised when Prometheus cannot supply the requested data."""


class PrometheusTargetUnavailableError(PrometheusError):
    """Raised when a requested Prometheus target is not healthy."""


class PrometheusMetricsMissingError(PrometheusError):
    """Raised when Prometheus has no usable samples for requested metrics."""


@dataclass(frozen=True)
class HostMetricObservation:
    timestamp: datetime
    cpu_percent: float
    memory_percent: float


class PrometheusClient:
    def __init__(
        self,
        base_url: str,
        *,
        timeout_seconds: float = 10.0,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._client = httpx.Client(
            base_url=self._base_url,
            timeout=timeout_seconds,
            transport=transport,
        )

    def close(self) -> None:
        self._client.close()

    def active_jobs(self) -> set[str]:
        payload = self._get_json("/api/v1/targets", {"state": "active"})
        targets = payload.get("data", {}).get("activeTargets", [])
        return {
            target.get("labels", {}).get("job", "")
            for target in targets
            if target.get("health") == "up"
            and target.get("labels", {}).get("job")
        }

    def require_active_job(self, job: str) -> None:
        if job not in self.active_jobs():
            raise PrometheusError(f"Prometheus job '{job}' has no active, healthy target.")

    def query_host_metrics(
        self,
        job: str = "windows-exporter",
        *,
        lookback_minutes: int = 60,
        step_seconds: int = 15,
    ) -> list[HostMetricObservation]:
        targets = self._get_json("/api/v1/targets", {"state": "active"})
        active_targets = targets.get("data", {}).get("activeTargets", [])
        job_targets = [
            target
            for target in active_targets
            if target.get("labels", {}).get("job") == job
        ]
        if not job_targets or not any(
            target.get("health") == "up" for target in job_targets
        ):
            raise PrometheusTargetUnavailableError(
                f"Windows Exporter Prometheus job '{job}' is not UP."
            )

        now = time.time()
        start = now - lookback_minutes * 60
        job_matcher = self._quote_label_value(job)
        expressions = {
            "cpu_percent": (
                "100 * (1 - avg by (instance) "
                "(rate(windows_cpu_time_seconds_total"
                f'{{job="{job_matcher}",mode="idle"}}[5m])))'
            ),
            "memory_percent": (
                "100 * (1 - windows_memory_physical_free_bytes"
                f'{{job="{job_matcher}"}} / windows_memory_physical_total_bytes'
                f'{{job="{job_matcher}"}})'
            ),
        }
        metric_values = {
            metric: self._range_query(
                expression,
                start=start,
                end=now,
                step_seconds=step_seconds,
            )
            for metric, expression in expressions.items()
        }
        valid_values = {
            metric: {
                timestamp: value
                for timestamp, value in values.items()
                if 0 <= value <= 100
            }
            for metric, values in metric_values.items()
        }
        timestamps = set.intersection(
            *(set(values) for values in valid_values.values())
        )
        if not timestamps:
            missing = [
                metric
                for metric, values in valid_values.items()
                if not values
            ]
            if missing:
                raise PrometheusMetricsMissingError(
                    "Prometheus returned no usable Windows "
                    f"{' and '.join(missing)} samples for job '{job}'."
                )
            raise PrometheusMetricsMissingError(
                "Prometheus returned no timestamp with complete Windows CPU and "
                f"memory samples for job '{job}'."
            )

        return [
            HostMetricObservation(
                timestamp=datetime.fromtimestamp(timestamp, timezone.utc),
                cpu_percent=valid_values["cpu_percent"][timestamp],
                memory_percent=valid_values["memory_percent"][timestamp],
            )
            for timestamp in sorted(timestamps)
        ]

    def query_range(
        self,
        job: str,
        *,
        lookback_minutes: int,
        step_seconds: int = 60,
    ) -> list[MetricObservation]:
        self.require_active_job(job)
        now = time.time()
        start = now - lookback_minutes * 60
        job_matcher = self._quote_label_value(job)
        expressions = {
            "cpu_cores": (
                "sum(rate(process_cpu_seconds_total"
                f'{{job="{job_matcher}"}}[5m]))'
            ),
            "memory_bytes": (
                "sum(process_resident_memory_bytes"
                f'{{job="{job_matcher}"}})'
            ),
            "request_rate": (
                "sum(rate(http_requests_total"
                f'{{job="{job_matcher}"}}[5m]))'
            ),
            "error_rate": (
                "sum(rate(http_requests_total"
                f'{{job="{job_matcher}",status=~"5.."}}[5m]))'
            ),
        }
        feature_values: dict[str, dict[float, float]] = {}
        for feature, expression in expressions.items():
            feature_values[feature] = self._range_query(
                expression,
                start=start,
                end=now,
                step_seconds=step_seconds,
            )

        base_features = ("cpu_cores", "memory_bytes", "request_rate")
        timestamps = set.intersection(
            *(set(feature_values[name]) for name in base_features)
        )
        if not timestamps:
            raise PrometheusError(
                f"Prometheus returned no complete CPU, memory, and request samples "
                f"for job '{job}'."
            )

        return [
            MetricObservation(
                timestamp=datetime.fromtimestamp(timestamp, timezone.utc),
                features={
                    name: (
                        feature_values[name].get(timestamp, 0.0)
                        if name == "error_rate"
                        else feature_values[name][timestamp]
                    )
                    for name in expressions
                },
            )
            for timestamp in sorted(timestamps)
        ]

    def _range_query(
        self,
        expression: str,
        *,
        start: float,
        end: float,
        step_seconds: int,
    ) -> dict[float, float]:
        payload = self._get_json(
            "/api/v1/query_range",
            {
                "query": expression,
                "start": start,
                "end": end,
                "step": f"{step_seconds}s",
            },
        )
        result = payload.get("data", {}).get("result", [])
        values_by_timestamp: dict[float, list[float]] = defaultdict(list)
        for series in result:
            for raw_timestamp, raw_value in series.get("values", []):
                try:
                    timestamp = float(raw_timestamp)
                    value = float(raw_value)
                except (TypeError, ValueError):
                    continue
                if math.isfinite(timestamp) and math.isfinite(value):
                    values_by_timestamp[timestamp].append(value)

        return {
            timestamp: sum(values) / len(values)
            for timestamp, values in values_by_timestamp.items()
        }

    def _get_json(self, path: str, params: dict[str, object]) -> dict[str, object]:
        try:
            response = self._client.get(path, params=params)
            response.raise_for_status()
            payload = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise PrometheusError(
                f"Unable to retrieve Prometheus data from {self._base_url}."
            ) from exc

        if not isinstance(payload, dict) or payload.get("status") != "success":
            message = payload.get("error", "unexpected Prometheus response") if isinstance(payload, dict) else "invalid JSON response"
            raise PrometheusError(f"Prometheus query failed: {message}")
        return payload

    @staticmethod
    def _quote_label_value(value: str) -> str:
        return value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")
