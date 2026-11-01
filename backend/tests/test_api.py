from datetime import datetime, timedelta, timezone

import pytest

from app.models.user import User, UserRole
from app.core.security import hash_password
from app.api.dependencies import get_prometheus_client
from app.main import app
from app.models.audit_log import AuditLog
from app.models.anomaly import Anomaly
from app.models.incident import Incident, IncidentSeverity
from app.models.infrastructure_resource import InfrastructureResource
from app.models.project import Project
from app.services.prometheus_service import (
    HostMetricObservation,
    PrometheusError,
    PrometheusMetricsMissingError,
    PrometheusTargetUnavailableError,
)
from ai_engine.anomaly_detector import MetricObservation
from conftest import TestingSessionLocal


def register(client, email="student@example.com", password="StrongPassword123"):
    return client.post(
        "/api/auth/register",
        json={
            "full_name": "AIOps Student",
            "email": email,
            "password": password,
        },
    )


def login(client, email="student@example.com", password="StrongPassword123"):
    return client.post(
        "/api/auth/login",
        data={"username": email, "password": password},
    )


class SyntheticPrometheusClient:
    def __init__(
        self,
        *,
        active_jobs=None,
        observations=None,
        host_observations=None,
        host_error=None,
    ):
        self._active_jobs = active_jobs or {"aiops-backend"}
        self._observations = observations or []
        self._host_observations = host_observations or []
        self._host_error = host_error

    def active_jobs(self):
        return self._active_jobs

    def query_host_metrics(self, job, *, lookback_minutes, step_seconds):
        assert job == "windows-exporter"
        assert lookback_minutes >= 5
        assert step_seconds >= 15
        if self._host_error is not None:
            raise self._host_error
        return self._host_observations

    def query_range(self, job, *, lookback_minutes):
        assert job == "aiops-backend"
        assert lookback_minutes > 0
        return self._observations

    def close(self):
        pass


def synthetic_observations():
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    observations = [
        MetricObservation(
            timestamp=start + timedelta(minutes=index),
            features={
                "cpu_cores": 0.05 + (index % 7) * 0.002,
                "memory_bytes": 100_000_000 + (index % 5) * 100_000,
                "request_rate": 1.0 + (index % 3) * 0.05,
                "error_rate": 0.0,
            },
        )
        for index in range(80)
    ]
    observations[-1] = MetricObservation(
        timestamp=observations[-1].timestamp,
        features={
            "cpu_cores": 8.0,
            "memory_bytes": 8_000_000_000,
            "request_rate": 80.0,
            "error_rate": 12.0,
        },
    )
    return observations


def test_health_endpoint_checks_database(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "connected"}


def test_prometheus_metrics_endpoint_exposes_http_metrics(client):
    client.get("/api/health")
    response = client.get("/metrics")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/plain")
    assert "http_requests_total" in response.text
    assert 'handler="/api/health"' in response.text


def test_registration_stores_hashed_password_and_defaults_to_viewer(client):
    response = register(client)
    assert response.status_code == 201
    assert response.json()["role"] == "viewer"
    assert "hashed_password" not in response.json()
    with TestingSessionLocal() as db:
        stored_user = db.query(User).filter_by(email="student@example.com").one()
        assert stored_user.hashed_password != "StrongPassword123"
        assert stored_user.hashed_password.startswith("$argon2")


def test_duplicate_registration_is_rejected(client):
    assert register(client).status_code == 201
    response = register(client)
    assert response.status_code == 409


def test_login_returns_token_and_me_is_protected(client):
    register(client)
    response = login(client)
    assert response.status_code == 200
    token = response.json()["access_token"]

    me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json()["email"] == "student@example.com"


def test_invalid_password_is_rejected(client):
    register(client)
    response = login(client, password="IncorrectPassword123")
    assert response.status_code == 401


def test_protected_endpoints_require_authentication(client):
    for path in (
        "/api/auth/me",
        "/api/dashboard/overview",
        "/api/monitoring/host-metrics",
        "/api/monitoring/resources",
        "/api/projects",
        "/api/anomalies",
        "/api/incidents",
        "/api/deployments",
        "/api/admin/users",
    ):
        assert client.get(path).status_code == 401


def test_host_metrics_returns_authenticated_timestamped_windows_samples(client):
    register(client)
    token = login(client).json()["access_token"]
    app.dependency_overrides[get_prometheus_client] = lambda: SyntheticPrometheusClient(
        host_observations=[
            HostMetricObservation(
                timestamp=datetime(2026, 1, 1, tzinfo=timezone.utc),
                cpu_percent=42.5,
                memory_percent=61.25,
            )
        ]
    )

    response = client.get(
        "/api/monitoring/host-metrics?lookback_minutes=30&step_seconds=30",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    result = response.json()
    assert result["job"] == "windows-exporter"
    assert result["lookback_minutes"] == 30
    assert result["step_seconds"] == 30
    assert result["samples"] == [
        {
            "timestamp": "2026-01-01T00:00:00Z",
            "cpu_percent": 42.5,
            "memory_percent": 61.25,
        }
    ]
    assert result["queried_at"]


@pytest.mark.parametrize(
    ("error", "expected_detail"),
    [
        (
            PrometheusTargetUnavailableError("Windows Exporter job is not UP."),
            "Windows Exporter job is not UP.",
        ),
        (
            PrometheusMetricsMissingError("Windows metrics are missing."),
            "Windows metrics are missing.",
        ),
        (PrometheusError("connection refused"), "Prometheus is unavailable."),
    ],
)
def test_host_metrics_maps_prometheus_failures_to_service_unavailable(
    client,
    error,
    expected_detail,
):
    register(client)
    token = login(client).json()["access_token"]
    app.dependency_overrides[get_prometheus_client] = lambda: SyntheticPrometheusClient(
        host_error=error
    )

    response = client.get(
        "/api/monitoring/host-metrics",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 503
    assert response.json()["detail"] == expected_detail


@pytest.mark.parametrize(
    "query",
    [
        "?lookback_minutes=4",
        "?lookback_minutes=1441",
        "?step_seconds=14",
        "?step_seconds=301",
        "?lookback_minutes=1440&step_seconds=15",
    ],
)
def test_host_metrics_rejects_out_of_range_query_parameters(client, query):
    register(client)
    token = login(client).json()["access_token"]

    response = client.get(
        f"/api/monitoring/host-metrics{query}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 422


def test_viewer_cannot_access_admin_user_list(client):
    register(client)
    token = login(client).json()["access_token"]
    response = client.get("/api/admin/users", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 403


def test_admin_can_access_admin_user_list(client):
    register(client)
    with TestingSessionLocal() as db:
        admin = User(
            full_name="Admin",
            email="admin@example.com",
            hashed_password=hash_password("AdminPassword123"),
            role=UserRole.ADMIN,
        )
        db.add(admin)
        db.commit()

    token = login(client, "admin@example.com", "AdminPassword123").json()["access_token"]
    response = client.get("/api/admin/users", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert len(response.json()) == 2


def test_registration_cannot_assign_admin_role(client):
    response = client.post(
        "/api/auth/register",
        json={
            "full_name": "AIOps Student",
            "email": "student@example.com",
            "password": "StrongPassword123",
            "role": "admin",
        },
    )
    assert response.status_code == 201
    assert response.json()["role"] == "viewer"


def test_dashboard_reports_empty_database_state(client):
    register(client)
    token = login(client).json()["access_token"]
    response = client.get(
        "/api/dashboard/overview",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json()["data_source"] == "database"
    assert response.json()["monitoring_connected"] is False
    assert response.json()["total_monitored_resources"] == 0
    assert response.json()["recent_activity"][0]["action"] == "user_registered"


def test_dashboard_only_includes_data_owned_by_current_user(client):
    register(client)
    token = login(client).json()["access_token"]
    with TestingSessionLocal() as db:
        other_user = User(
            full_name="Other User",
            email="other@example.com",
            hashed_password=hash_password("OtherPassword123"),
            role=UserRole.VIEWER,
        )
        db.add(other_user)
        db.flush()
        project = Project(name="Other user's project", owner_id=other_user.id)
        db.add(project)
        db.flush()
        resource = InfrastructureResource(
            project_id=project.id,
            resource_name="other-resource",
            resource_type="prometheus_job",
        )
        incident = Incident(
            project_id=project.id,
            title="Other user's incident",
            severity=IncidentSeverity.HIGH,
        )
        db.add_all(
            [
                resource,
                incident,
                AuditLog(
                    user_id=other_user.id,
                    action="other_user_action",
                    resource_type="project",
                ),
            ]
        )
        db.commit()

    response = client.get(
        "/api/dashboard/overview",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json()["total_monitored_resources"] == 0
    assert response.json()["open_incidents"] == 0
    assert [entry["action"] for entry in response.json()["recent_activity"]] == [
        "user_registered"
    ]


def test_prometheus_anomaly_detection_creates_incidents_idempotently(client):
    registration = register(client)
    assert registration.status_code == 201
    token = login(client).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    app.dependency_overrides[get_prometheus_client] = lambda: SyntheticPrometheusClient(
        observations=synthetic_observations()
    )

    project_response = client.post(
        "/api/projects",
        json={"name": "Local AIOps test", "description": "Synthetic API test fixture"},
        headers=headers,
    )
    assert project_response.status_code == 201
    project_id = project_response.json()["id"]
    assert project_response.json()["environment"] == "local"

    resource_response = client.post(
        "/api/monitoring/resources",
        json={"project_id": project_id, "prometheus_job": "aiops-backend"},
        headers=headers,
    )
    assert resource_response.status_code == 201
    resource_id = resource_response.json()["id"]

    detection_response = client.post(
        "/api/anomalies/detect",
        json={"resource_id": resource_id},
        headers=headers,
    )
    assert detection_response.status_code == 200
    result = detection_response.json()
    assert result["sample_count"] == 80
    assert result["anomaly_count"] >= 1
    assert result["incidents_created"] == result["anomaly_count"]
    assert all(item["incident_id"] for item in result["anomalies"])
    assert all(item["resource"] == "aiops-backend" for item in result["anomalies"])

    repeated_response = client.post(
        "/api/anomalies/detect",
        json={"resource_id": resource_id},
        headers=headers,
    )
    assert repeated_response.status_code == 200
    assert repeated_response.json()["anomaly_count"] == 0

    incidents_response = client.get("/api/incidents", headers=headers)
    assert incidents_response.status_code == 200
    assert len(incidents_response.json()) == result["incidents_created"]
    with TestingSessionLocal() as db:
        assert db.query(Anomaly).count() == result["anomaly_count"]
        assert db.query(Incident).count() == result["incidents_created"]
        assert (
            db.query(AuditLog)
            .filter_by(action="anomaly_detection_completed")
            .count()
            == 2
        )


def test_monitoring_resource_registration_rejects_unhealthy_job(client):
    register(client)
    token = login(client).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    app.dependency_overrides[get_prometheus_client] = lambda: SyntheticPrometheusClient(
        active_jobs={"prometheus"}
    )
    project = client.post(
        "/api/projects",
        json={"name": "Local project"},
        headers=headers,
    ).json()

    response = client.post(
        "/api/monitoring/resources",
        json={"project_id": project["id"], "prometheus_job": "aiops-backend"},
        headers=headers,
    )

    assert response.status_code == 422
    assert response.json()["detail"] == "The Prometheus job has no active, healthy target."


def test_anomaly_detection_requires_owned_registered_resource(client):
    register(client)
    token = login(client).json()["access_token"]
    response = client.post(
        "/api/anomalies/detect",
        json={"resource_id": "00000000-0000-0000-0000-000000000001"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Monitoring resource not found."
