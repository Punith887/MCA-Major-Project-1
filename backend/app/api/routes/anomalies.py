from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ai_engine.anomaly_detector import InsufficientMetricsError, detect_anomalies
from app.api.dependencies import get_current_user, get_prometheus_client
from app.core.config import get_settings
from app.database.connection import get_db
from app.models.anomaly import Anomaly
from app.models.infrastructure_resource import InfrastructureResource
from app.models.project import Project
from app.models.user import User
from app.schemas.anomaly import (
    AnomalyDetectionRequest,
    AnomalyDetectionResult,
    AnomalyRead,
)
from app.services.anomaly_service import persist_anomalies
from app.services.prometheus_service import PrometheusClient, PrometheusError

router = APIRouter(prefix="/anomalies", tags=["anomalies"])


@router.get("", response_model=list[AnomalyRead])
def list_anomalies(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[AnomalyRead]:
    records = db.execute(
        select(Anomaly, InfrastructureResource.resource_name)
        .join(
            InfrastructureResource,
            InfrastructureResource.id == Anomaly.resource_id,
        )
        .join(Project, Project.id == InfrastructureResource.project_id)
        .where(Project.owner_id == user.id)
        .order_by(Anomaly.detected_at.desc())
    ).all()
    return [
        AnomalyRead(
            id=anomaly.id,
            resource_id=anomaly.resource_id,
            resource=resource_name,
            incident_id=anomaly.incident_id,
            detected_at=anomaly.detected_at,
            anomaly_score=anomaly.anomaly_score,
            detected_features=anomaly.detected_features,
            severity=anomaly.severity,
            status=anomaly.status,
            created_at=anomaly.created_at,
        )
        for anomaly, resource_name in records
    ]


@router.post("/detect", response_model=AnomalyDetectionResult)
def run_detection(
    payload: AnomalyDetectionRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    prometheus: PrometheusClient = Depends(get_prometheus_client),
) -> AnomalyDetectionResult:
    resource = db.scalar(
        select(InfrastructureResource)
        .join(Project, Project.id == InfrastructureResource.project_id)
        .where(
            InfrastructureResource.id == payload.resource_id,
            Project.owner_id == user.id,
        )
    )
    if resource is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Monitoring resource not found.",
        )
    if not resource.prometheus_job:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Monitoring resource is not linked to a Prometheus job.",
        )

    settings = get_settings()
    try:
        observations = prometheus.query_range(
            resource.prometheus_job,
            lookback_minutes=settings.anomaly_lookback_minutes,
        )
    except PrometheusError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc

    try:
        scored_observations = detect_anomalies(
            observations,
            minimum_samples=settings.anomaly_minimum_samples,
            contamination=settings.anomaly_contamination,
        )
    except InsufficientMetricsError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

    created, incidents_created = persist_anomalies(
        db,
        user.id,
        resource,
        scored_observations,
    )
    return AnomalyDetectionResult(
        resource_id=resource.id,
        prometheus_job=resource.prometheus_job,
        sample_count=len(observations),
        lookback_minutes=settings.anomaly_lookback_minutes,
        anomaly_count=len(created),
        incidents_created=incidents_created,
        anomalies=[
            AnomalyRead(
                id=anomaly.id,
                resource_id=anomaly.resource_id,
                resource=resource.resource_name,
                incident_id=anomaly.incident_id,
                detected_at=anomaly.detected_at,
                anomaly_score=anomaly.anomaly_score,
                detected_features=anomaly.detected_features,
                severity=anomaly.severity,
                status=anomaly.status,
                created_at=anomaly.created_at,
            )
            for anomaly in created
        ],
    )
