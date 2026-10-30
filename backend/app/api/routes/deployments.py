from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.database.connection import get_db
from app.models.deployment import Deployment
from app.models.user import User
from app.schemas.deployment import DeploymentRead

router = APIRouter(prefix="/deployments", tags=["deployments"])


@router.get("", response_model=list[DeploymentRead])
def list_deployments(
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[Deployment]:
    return list(db.scalars(select(Deployment).order_by(Deployment.created_at.desc())).all())
