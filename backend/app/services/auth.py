from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import hash_password, verify_password
from app.models.audit_log import AuditLog
from app.models.user import User, UserRole
from app.schemas.auth import UserRegister


def register_user(db: Session, payload: UserRegister) -> User:
    normalized_email = str(payload.email).strip().lower()
    existing_user = db.scalar(select(User).where(User.email == normalized_email))
    if existing_user is not None:
        raise ValueError("An account with this email already exists.")

    user = User(
        full_name=payload.full_name.strip(),
        email=normalized_email,
        hashed_password=hash_password(payload.password),
        role=UserRole.VIEWER,
    )
    db.add(user)
    db.flush()
    db.add(
        AuditLog(
            user_id=user.id,
            action="user_registered",
            resource_type="user",
            resource_id=str(user.id),
        )
    )
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: Session, email: str, password: str) -> User | None:
    normalized_email = email.strip().lower()
    user = db.scalar(select(User).where(User.email == normalized_email))
    if user is None or not user.is_active or not verify_password(password, user.hashed_password):
        return None
    return user
