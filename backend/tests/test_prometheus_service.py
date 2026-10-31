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
