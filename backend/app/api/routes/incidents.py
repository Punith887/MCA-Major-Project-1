from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.database.connection import get_db
from app.models.incident import Incident
from app.models.user import User
from app.schemas.incident import IncidentRead

router = APIRouter(prefix="/incidents", tags=["incidents"])


@router.get("", response_model=list[IncidentRead])
def list_incidents(
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[Incident]:
    return list(db.scalars(select(Incident).order_by(Incident.detected_at.desc())).all())
