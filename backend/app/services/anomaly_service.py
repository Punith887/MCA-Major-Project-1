from collections.abc import Sequence
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from ai_engine.anomaly_detector import ScoredObservation
from app.models.audit_log import AuditLog
from app.models.anomaly import Anomaly
from app.models.incident import Incident, IncidentSeverity
from app.models.infrastructure_resource import InfrastructureResource


def persist_anomalies(
    db: Session,
    user_id: UUID,
    resource: InfrastructureResource,
    observations: Sequence[ScoredObservation],
) -> tuple[list[Anomaly], int]:
    anomalous_observations = [item for item in observations if item.is_anomaly]
    timestamps = [item.timestamp for item in anomalous_observations]
    existing_timestamps: set[datetime] = set()
    if timestamps:
        existing_timestamps = {
            _timestamp_key(timestamp)
            for timestamp in db.scalars(
                select(Anomaly.detected_at).where(
                    Anomaly.resource_id == resource.id,
                    Anomaly.detected_at.in_(timestamps),
                )
            ).all()
        }

    created: list[Anomaly] = []
    try:
        for observation in anomalous_observations:
            if _timestamp_key(observation.timestamp) in existing_timestamps:
                continue

            anomaly = Anomaly(
                resource_id=resource.id,
                detected_at=observation.timestamp,
                anomaly_score=observation.anomaly_score,
                detected_features=observation.features,
                severity="medium",
                status="detected",
            )
            db.add(anomaly)
            db.flush()
            existing_timestamps.add(_timestamp_key(observation.timestamp))

            incident = Incident(
                project_id=resource.project_id,
                title=f"Anomaly detected for {resource.resource_name}",
                description=(
                    "Isolation Forest flagged an observed Prometheus sample. "
                    "The anomaly score is the negated decision function, not a "
                    "probability. "
                    f"Score: {observation.anomaly_score:.6f}; "
                    f"features: {observation.features}"
                ),
                severity=IncidentSeverity.MEDIUM,
            )
            db.add(incident)
            db.flush()
            anomaly.incident_id = incident.id
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
                    "incidents_created": len(created),
                },
            )
        )
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        raise

    for anomaly in created:
        db.refresh(anomaly)
    return created, len(created)


def _timestamp_key(timestamp: datetime) -> datetime:
    if timestamp.tzinfo is None:
        return timestamp
    return timestamp.astimezone(timezone.utc).replace(tzinfo=None)
