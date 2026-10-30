from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.database.connection import get_db
from app.models.infrastructure_resource import InfrastructureResource
from app.models.user import User
from app.schemas.infrastructure import ResourceRead

router = APIRouter(prefix="/monitoring", tags=["monitoring"])


@router.get("/resources", response_model=list[ResourceRead])
def list_resources(
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[InfrastructureResource]:
    return list(
        db.scalars(
            select(InfrastructureResource).order_by(InfrastructureResource.created_at.desc())
        ).all()
    )
