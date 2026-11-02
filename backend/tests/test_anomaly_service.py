from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest

from ai_engine.anomaly_detector import ScoredObservation
from app.core.config import Settings
from app.models.anomaly import Anomaly
from app.models.incident import Incident, IncidentSeverity, IncidentStatus
from app.models.infrastructure_resource import InfrastructureResource
from app.models.project import Project
from app.models.user import User
from app.services.anomaly_service import (
    classify_metric_severity,
    persist_anomalies,
)
from app.core.security import hash_password
from conftest import TestingSessionLocal


def create_monitoring_resources(
    *,
    resource_count: int,
    project_count: int,
) -> tuple[User, list[InfrastructureResource]]:
    user = User(
        full_name="AIOps Test User",
        email=f"{uuid4()}@example.com",
        hashed_password=hash_password("StrongPassword123"),
    )
    projects = [
        Project(name=f"Test project {index}", owner=user)
        for index in range(project_count)
    ]
    resources = [
        InfrastructureResource(
            project=projects[index % project_count],
            resource_name=f"resource-{index}",
            resource_type="prometheus_job",
        )
        for index in range(resource_count)
    ]
    with TestingSessionLocal() as db:
        db.add_all([user, *projects, *resources])
        db.commit()
        db.refresh(user)
        for resource in resources:
            db.refresh(resource)
    return user, resources


def observation(
    minute: int,
    *,
    features: dict[str, float] | None = None,
    is_anomaly: bool = True,
) -> ScoredObservation:
    return ScoredObservation(
        timestamp=datetime(2026, 1, 1, tzinfo=timezone.utc) + timedelta(minutes=minute),
        features=features
        or {
            "cpu_cores": 0.1,
            "memory_bytes": 100_000_000,
            "request_rate": 1.0,
            "error_rate": 0.0,
        },
        anomaly_score=0.01,
        is_anomaly=is_anomaly,
    )


def test_same_resource_anomalies_share_incident_and_timestamp_deduplication(client):
    user, resources = create_monitoring_resources(resource_count=1, project_count=1)
    observations = [observation(0), observation(1), observation(1)]
    with TestingSessionLocal() as db:
        created, incidents_created = persist_anomalies(
            db, user.id, resources[0], observations
        )
        repeated, repeated_incidents = persist_anomalies(
            db, user.id, resources[0], observations
        )

        assert len(created) == 2
        assert incidents_created == 1
        assert repeated == []
        assert repeated_incidents == 0
        assert len({anomaly.incident_id for anomaly in created}) == 1
        assert all(anomaly.incident_id is not None for anomaly in created)
        assert db.query(Anomaly).count() == 2
        assert db.query(Incident).count() == 1
        incident = db.query(Incident).one()
        assert incident.resource_id == resources[0].id


def test_isolation_forest_score_does_not_raise_metric_severity(client):
    user, resources = create_monitoring_resources(resource_count=1, project_count=1)
    sample = observation(0)
    sample = ScoredObservation(
        timestamp=sample.timestamp,
        features=sample.features,
        anomaly_score=1000.0,
        is_anomaly=True,
    )
    with TestingSessionLocal() as db:
        created, _ = persist_anomalies(db, user.id, resources[0], [sample])

        assert created[0].severity == IncidentSeverity.LOW.value
        incident = db.get(Incident, created[0].incident_id)
        assert incident is not None
        assert incident.severity == IncidentSeverity.LOW


def test_acknowledged_incident_is_reused_and_resolved_incident_is_replaced(client):
    user, resources = create_monitoring_resources(resource_count=1, project_count=1)
    with TestingSessionLocal() as db:
        first, created_count = persist_anomalies(
            db, user.id, resources[0], [observation(0)]
        )
        incident_id = first[0].incident_id
        incident = db.get(Incident, incident_id)
        assert incident is not None
        incident.status = IncidentStatus.ACKNOWLEDGED
        db.commit()

        acknowledged, acknowledged_count = persist_anomalies(
            db, user.id, resources[0], [observation(1)]
        )
        assert acknowledged_count == 0
        assert acknowledged[0].incident_id == incident_id

        incident.status = IncidentStatus.RESOLVED
        db.commit()
        after_resolution, new_incident_count = persist_anomalies(
            db, user.id, resources[0], [observation(2)]
        )

        assert created_count == 1
        assert new_incident_count == 1
        assert after_resolution[0].incident_id != incident_id
        assert db.query(Incident).count() == 2


def test_different_resources_and_projects_never_share_incidents(client):
    user, resources = create_monitoring_resources(resource_count=3, project_count=2)
    incident_ids = []
    with TestingSessionLocal() as db:
        for index, resource in enumerate(resources):
            created, incident_count = persist_anomalies(
                db, user.id, resource, [observation(index)]
            )
            assert incident_count == 1
            assert len(created) == 1
            incident_ids.append(created[0].incident_id)

        assert len(set(incident_ids)) == 3
        incidents = [db.get(Incident, incident_id) for incident_id in incident_ids]
        assert all(incident is not None for incident in incidents)
        assert [
            (incident.resource_id, incident.project_id) for incident in incidents
        ] == [(resource.id, resource.project_id) for resource in resources]


@pytest.mark.parametrize(
    ("features", "expected"),
    [
        ({"cpu_cores": 0.49}, IncidentSeverity.LOW),
        ({"cpu_cores": 0.5}, IncidentSeverity.MEDIUM),
        ({"cpu_cores": 1.0}, IncidentSeverity.HIGH),
        ({"memory_bytes": 2_147_483_648}, IncidentSeverity.CRITICAL),
        ({"error_rate": 1.0}, IncidentSeverity.HIGH),
        (
            {"cpu_cores": 0.5, "error_rate": 1.0},
            IncidentSeverity.HIGH,
        ),
    ],
)
def test_metric_evidence_classifies_severity(features, expected):
    assert classify_metric_severity(features) == expected


def test_severity_thresholds_are_configurable_and_validated():
    settings = Settings(
        environment="test",
        secret_key="test-only-secret-key-not-for-production",
        anomaly_severity_medium_cpu_cores=0.25,
        anomaly_severity_high_cpu_cores=0.75,
        anomaly_severity_critical_cpu_cores=1.5,
    )
    assert (
        classify_metric_severity({"cpu_cores": 0.3}, settings=settings)
        == IncidentSeverity.MEDIUM
    )

    with pytest.raises(ValueError, match="must increase"):
        Settings(
            environment="test",
            secret_key="test-only-secret-key-not-for-production",
            anomaly_severity_medium_cpu_cores=1.0,
            anomaly_severity_high_cpu_cores=0.5,
        )


def test_new_anomaly_escalates_active_incident_to_highest_metric_severity(client):
    user, resources = create_monitoring_resources(resource_count=1, project_count=1)
    with TestingSessionLocal() as db:
        first, _ = persist_anomalies(
            db,
            user.id,
            resources[0],
            [observation(0, features={"cpu_cores": 0.5})],
        )
        incident = db.get(Incident, first[0].incident_id)
        assert incident is not None
        assert incident.severity == IncidentSeverity.MEDIUM

        second, incident_count = persist_anomalies(
            db,
            user.id,
            resources[0],
            [observation(1, features={"error_rate": 5.0})],
        )

        assert incident_count == 0
        assert second[0].incident_id == first[0].incident_id
        assert second[0].severity == IncidentSeverity.CRITICAL.value
        assert incident.severity == IncidentSeverity.CRITICAL
