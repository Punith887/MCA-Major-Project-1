from collections.abc import Sequence
from datetime import datetime, timezone
import math
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from ai_engine.anomaly_detector import ScoredObservation
from app.core.config import Settings, get_settings
from app.models.audit_log import AuditLog
from app.models.anomaly import Anomaly
from app.models.incident import Incident, IncidentSeverity, IncidentStatus
from app.models.infrastructure_resource import InfrastructureResource


class MonitoredResourceUnavailableError(ValueError):
    """Raised when a monitored resource is deleted before its results are persisted."""


def persist_anomalies(
    db: Session,
    user_id: UUID,
    resource: InfrastructureResource,
    observations: Sequence[ScoredObservation],
) -> tuple[list[Anomaly], int]:
    anomalous_observations = [item for item in observations if item.is_anomaly]
    created: list[Anomaly] = []
    incidents_created = 0
    try:
        locked_resource = db.scalar(
            select(InfrastructureResource)
            .where(InfrastructureResource.id == resource.id)
            .with_for_update()
        )
        if locked_resource is None:
            raise MonitoredResourceUnavailableError(
                "Monitoring resource no longer exists."
            )

        timestamps = [item.timestamp for item in anomalous_observations]
        existing_timestamps: set[datetime] = set()
        if timestamps:
            existing_timestamps = {
                _timestamp_key(timestamp)
                for timestamp in db.scalars(
                    select(Anomaly.detected_at).where(
                        Anomaly.resource_id == locked_resource.id,
                        Anomaly.detected_at.in_(timestamps),
                    )
                ).all()
            }

        new_observations: list[ScoredObservation] = []
        for item in anomalous_observations:
            timestamp_key = _timestamp_key(item.timestamp)
            if timestamp_key not in existing_timestamps:
                new_observations.append(item)
                existing_timestamps.add(timestamp_key)
        settings = get_settings()
        active_incident = None
        if new_observations:
            active_incident = db.scalar(
                select(Incident)
                .where(
                    Incident.resource_id == locked_resource.id,
                    Incident.project_id == locked_resource.project_id,
                    Incident.status.in_(
                        [IncidentStatus.OPEN, IncidentStatus.ACKNOWLEDGED]
                    ),
                )
                .order_by(Incident.detected_at.desc())
                .limit(1)
            )

        for observation in new_observations:
            severity = classify_metric_severity(observation.features, settings=settings)
            anomaly = Anomaly(
                resource_id=locked_resource.id,
                detected_at=observation.timestamp,
                anomaly_score=observation.anomaly_score,
                detected_features=observation.features,
                severity=severity.value,
                status="detected",
            )
            db.add(anomaly)
            db.flush()
            existing_timestamps.add(_timestamp_key(observation.timestamp))

            if active_incident is None:
                active_incident = Incident(
                    project_id=locked_resource.project_id,
                    resource_id=locked_resource.id,
                    title=f"Anomaly detected for {locked_resource.resource_name}",
                    description=(
                        "Isolation Forest flagged an observed Prometheus sample. "
                        "The anomaly score is the negated decision function, not a "
                        "probability. "
                        "Severity is based on configured CPU, memory, and HTTP 5xx "
                        "request-rate thresholds. "
                        f"Score: {observation.anomaly_score:.6f}; "
                        f"features: {observation.features}"
                    ),
                    severity=severity,
                )
                db.add(active_incident)
                db.flush()
                incidents_created += 1
            elif _severity_rank(severity) > _severity_rank(active_incident.severity):
                active_incident.severity = severity

            anomaly.incident_id = active_incident.id
            created.append(anomaly)

        db.add(
            AuditLog(
                user_id=user_id,
                action="anomaly_detection_completed",
                resource_type="infrastructure_resource",
                resource_id=str(resource.id),
                details={
                    "sample_count": len(observations),
                    "anomalies_created": len(created),
                    "incidents_created": incidents_created,
                },
            )
        )
        db.commit()
    except MonitoredResourceUnavailableError:
        db.rollback()
        raise
    except SQLAlchemyError:
        db.rollback()
        raise

    for anomaly in created:
        db.refresh(anomaly)
    return created, incidents_created


def classify_metric_severity(
    features: dict[str, float],
    *,
    settings: Settings | None = None,
) -> IncidentSeverity:
    """Classify observed load/error evidence; Isolation Forest scores are not used."""
    settings = settings or get_settings()
    severity = IncidentSeverity.LOW
    thresholds = {
        "cpu_cores": (
            settings.anomaly_severity_medium_cpu_cores,
            settings.anomaly_severity_high_cpu_cores,
            settings.anomaly_severity_critical_cpu_cores,
        ),
        "memory_bytes": (
            settings.anomaly_severity_medium_memory_bytes,
            settings.anomaly_severity_high_memory_bytes,
            settings.anomaly_severity_critical_memory_bytes,
        ),
        "error_rate": (
            settings.anomaly_severity_medium_error_rate,
            settings.anomaly_severity_high_error_rate,
            settings.anomaly_severity_critical_error_rate,
        ),
    }

    for metric, metric_thresholds in thresholds.items():
        value = features.get(metric)
        if value is None or not math.isfinite(value):
            continue
        metric_severity = IncidentSeverity.LOW
        for candidate, threshold in zip(
            (
                IncidentSeverity.MEDIUM,
                IncidentSeverity.HIGH,
                IncidentSeverity.CRITICAL,
            ),
            metric_thresholds,
            strict=True,
        ):
            if value >= threshold:
                metric_severity = candidate
        if _severity_rank(metric_severity) > _severity_rank(severity):
            severity = metric_severity

    return severity


def _severity_rank(severity: IncidentSeverity) -> int:
    return {
        IncidentSeverity.LOW: 0,
        IncidentSeverity.MEDIUM: 1,
        IncidentSeverity.HIGH: 2,
        IncidentSeverity.CRITICAL: 3,
    }[severity]


def _timestamp_key(timestamp: datetime) -> datetime:
    if timestamp.tzinfo is None:
        return timestamp
    return timestamp.astimezone(timezone.utc).replace(tzinfo=None)
