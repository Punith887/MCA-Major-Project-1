from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.database.connection import get_db
from app.models.audit_log import AuditLog
from app.models.project import Project
from app.models.user import User
from app.schemas.project import ProjectCreate, ProjectRead

router = APIRouter(prefix="/projects", tags=["projects"])


@router.get("", response_model=list[ProjectRead])
def list_projects(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[Project]:
    return list(
        db.scalars(
            select(Project)
            .where(Project.owner_id == user.id)
            .order_by(Project.created_at.desc())
        ).all()
    )


@router.post("", response_model=ProjectRead, status_code=status.HTTP_201_CREATED)
def create_project(
    payload: ProjectCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Project:
    project = Project(
        name=payload.name.strip(),
        description=payload.description,
        environment="local",
        owner_id=user.id,
    )
    db.add(project)
    db.flush()
    db.add(
        AuditLog(
            user_id=user.id,
            action="project_created",
            resource_type="project",
            resource_id=str(project.id),
            details={"environment": "local"},
        )
    )
    db.commit()
    db.refresh(project)
    return project
