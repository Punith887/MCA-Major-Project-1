from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.permissions import require_roles
from app.database.connection import get_db
from app.models.user import User, UserRole
from app.schemas.auth import UserRead

router = APIRouter(prefix="/admin", tags=["administration"])


@router.get("/users", response_model=list[UserRead])
def list_users(
    _: User = Depends(require_roles(UserRole.ADMIN)),
    db: Session = Depends(get_db),
) -> list[User]:
    return list(db.scalars(select(User).order_by(User.created_at.desc())).all())
