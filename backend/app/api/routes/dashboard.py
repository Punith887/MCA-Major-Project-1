from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.database.connection import get_db
from app.models.audit_log import AuditLog
from app.models.deployment import Deployment
from app.models.incident import Incident, IncidentStatus
from app.models.infrastructure_resource import InfrastructureResource, ResourceStatus
from app.models.project import Project
from app.models.user import User
from app.schemas.dashboard import ActivityItem, DashboardOverview

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/overview", response_model=DashboardOverview)
def get_overview(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DashboardOverview:
    resource_counts = dict(
        db.execute(
            select(InfrastructureResource.status, func.count(InfrastructureResource.id))
            .join(Project, Project.id == InfrastructureResource.project_id)
            .where(Project.owner_id == user.id)
            .group_by(InfrastructureResource.status)
        ).all()
    )
    active_incidents = db.scalar(
        select(func.count(Incident.id))
        .join(Project, Project.id == Incident.project_id)
        .where(
            Project.owner_id == user.id,
            Incident.status != IncidentStatus.RESOLVED,
        )
    ) or 0
    recent_deployments = db.scalar(
        select(func.count(Deployment.id))
        .join(Project, Project.id == Deployment.project_id)
        .where(
            Project.owner_id == user.id,
            Deployment.created_at >= datetime.now(timezone.utc) - timedelta(days=7),
        )
    ) or 0
    activity_rows = db.scalars(
        select(AuditLog)
        .where(AuditLog.user_id == user.id)
        .order_by(AuditLog.created_at.desc())
        .limit(5)
    ).all()

    return DashboardOverview(
        total_monitored_resources=sum(resource_counts.values()),
        healthy_resources=resource_counts.get(ResourceStatus.HEALTHY, 0),
        warning_resources=resource_counts.get(ResourceStatus.WARNING, 0),
        critical_resources=resource_counts.get(ResourceStatus.CRITICAL, 0),
        open_incidents=active_incidents,
        recent_deployments=recent_deployments,
        recent_activity=[
            ActivityItem(
                action=entry.action,
                resource_type=entry.resource_type,
                created_at=entry.created_at,
            )
            for entry in activity_rows
        ],
    )
