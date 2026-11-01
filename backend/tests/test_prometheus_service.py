import httpx
import pytest

from app.services.prometheus_service import PrometheusClient, PrometheusError


def test_range_query_builds_complete_metric_observations():
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/api/v1/targets":
            payload = {
                "status": "success",
                "data": {
                    "activeTargets": [
                        {"labels": {"job": "aiops-backend"}, "health": "up"}
                    ]
                },
            }
        elif request.url.path == "/api/v1/query_range":
            expression = request.url.params["query"]
            values = [["1000", "0.1"], ["1060", "0.2"]]
            if "process_resident_memory_bytes" in expression:
                values = [["1000", "1000000"], ["1060", "1100000"]]
            elif "http_requests_total" in expression and 'status=~"5.."' not in expression:
                values = [["1000", "1.5"], ["1060", "2.0"]]
            elif 'status=~"5.."' in expression:
                values = []
            payload = {
                "status": "success",
                "data": {
                    "result": [{"values": values}] if values else [],
                },
            }
        else:
            return httpx.Response(404)
        return httpx.Response(200, json=payload)

    client = PrometheusClient(
        "http://prometheus.test",
        transport=httpx.MockTransport(handler),
    )
    try:
        observations = client.query_range(
            "aiops-backend",
            lookback_minutes=60,
        )
    finally:
        client.close()

    assert len(observations) == 2
    assert observations[0].features == {
        "cpu_cores": 0.1,
        "memory_bytes": 1_000_000.0,
        "request_rate": 1.5,
        "error_rate": 0.0,
    }


def test_prometheus_job_must_be_active():
    client = PrometheusClient(
        "http://prometheus.test",
        transport=httpx.MockTransport(
            lambda _: httpx.Response(
                200,
                json={
                    "status": "success",
                    "data": {
                        "activeTargets": [
                            {"labels": {"job": "prometheus"}, "health": "up"}
                        ]
                    },
                },
            )
        ),
    )
    try:
        with pytest.raises(PrometheusError, match="no active, healthy target"):
            client.query_range("aiops-backend", lookback_minutes=60)
    finally:
        client.close()


def test_host_metric_query_returns_timestamped_cpu_and_memory_percentages():
    seen_queries = []

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/api/v1/targets":
            payload = {
                "status": "success",
                "data": {
                    "activeTargets": [
                        {"labels": {"job": "windows-exporter"}, "health": "up"}
                    ]
                },
            }
        elif request.url.path == "/api/v1/query_range":
            expression = request.url.params["query"]
            seen_queries.append(expression)
            values = [["1000", "30"], ["1060", "40"]]
            if "windows_memory_physical_free_bytes" in expression:
                values = [["1000", "60"], ["1060", "65"]]
            payload = {
                "status": "success",
                "data": {"result": [{"values": values}]},
            }
        else:
            return httpx.Response(404)
        return httpx.Response(200, json=payload)

    client = PrometheusClient(
        "http://prometheus.test",
        transport=httpx.MockTransport(handler),
    )
    try:
        observations = client.query_host_metrics(
            lookback_minutes=30,
            step_seconds=30,
        )
    finally:
        client.close()

    assert [sample.cpu_percent for sample in observations] == [30, 40]
    assert [sample.memory_percent for sample in observations] == [60, 65]
    assert observations[0].timestamp.isoformat() == "1970-01-01T00:16:40+00:00"
    assert len(seen_queries) == 2
    assert all('job="windows-exporter"' in query for query in seen_queries)
    assert any("windows_cpu_time_seconds_total" in query for query in seen_queries)
    assert any("windows_memory_physical_total_bytes" in query for query in seen_queries)


def test_host_metric_query_rejects_unhealthy_exporter():
    client = PrometheusClient(
        "http://prometheus.test",
        transport=httpx.MockTransport(
            lambda _: httpx.Response(
                200,
                json={
                    "status": "success",
                    "data": {
                        "activeTargets": [
                            {
                                "labels": {"job": "windows-exporter"},
                                "health": "down",
                            }
                        ]
                    },
                },
            )
        ),
    )
    try:
        with pytest.raises(PrometheusError, match="windows-exporter.*not UP"):
            client.query_host_metrics()
    finally:
        client.close()


def test_host_metric_query_rejects_missing_metric_samples():
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/api/v1/targets":
            payload = {
                "status": "success",
                "data": {
                    "activeTargets": [
                        {"labels": {"job": "windows-exporter"}, "health": "up"}
                    ]
                },
            }
        else:
            payload = {"status": "success", "data": {"result": []}}
        return httpx.Response(200, json=payload)

    client = PrometheusClient(
        "http://prometheus.test",
        transport=httpx.MockTransport(handler),
    )
    try:
        with pytest.raises(PrometheusError, match="no usable Windows"):
            client.query_host_metrics()
    finally:
        client.close()


def test_host_metric_query_reports_prometheus_connection_failure():
    def handler(_: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("connection refused")

    client = PrometheusClient(
        "http://prometheus.test",
        transport=httpx.MockTransport(handler),
    )
    try:
        with pytest.raises(PrometheusError, match="Unable to retrieve Prometheus data"):
            client.query_host_metrics()
    finally:
        client.close()
