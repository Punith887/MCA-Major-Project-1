from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, get_prometheus_client
from app.database.connection import get_db
from app.models.infrastructure_resource import InfrastructureResource
from app.models.project import Project
from app.models.user import User
from app.schemas.infrastructure import ResourceCreate, ResourceRead
from app.services.prometheus_service import PrometheusClient, PrometheusError

router = APIRouter(prefix="/monitoring", tags=["monitoring"])


@router.get("/resources", response_model=list[ResourceRead])
def list_resources(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[InfrastructureResource]:
    return list(
        db.scalars(
            select(InfrastructureResource)
            .join(Project, Project.id == InfrastructureResource.project_id)
            .where(Project.owner_id == user.id)
            .order_by(InfrastructureResource.created_at.desc())
        ).all()
    )


@router.post(
    "/resources",
    response_model=ResourceRead,
    status_code=status.HTTP_201_CREATED,
)
def register_prometheus_resource(
    payload: ResourceCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    prometheus: PrometheusClient = Depends(get_prometheus_client),
) -> InfrastructureResource:
    project = db.scalar(
        select(Project).where(
            Project.id == payload.project_id,
            Project.owner_id == user.id,
        )
    )
    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found.",
        )

    try:
        if payload.prometheus_job not in prometheus.active_jobs():
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="The Prometheus job has no active, healthy target.",
            )
    except PrometheusError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Prometheus is unavailable.",
        ) from exc

    existing = db.scalar(
        select(InfrastructureResource).where(
            InfrastructureResource.project_id == project.id,
            InfrastructureResource.prometheus_job == payload.prometheus_job,
        )
    )
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This Prometheus job is already registered for the project.",
        )

    resource = InfrastructureResource(
        project_id=project.id,
        resource_name=payload.prometheus_job,
        resource_type="prometheus_job",
        prometheus_job=payload.prometheus_job,
        environment="local",
    )
    db.add(resource)
    db.commit()
    db.refresh(resource)
    return resource
