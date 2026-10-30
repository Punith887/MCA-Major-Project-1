from collections.abc import Callable

from fastapi import Depends, HTTPException, status

from app.api.dependencies import get_current_user
from app.models.user import User, UserRole


def require_roles(*allowed_roles: UserRole) -> Callable[..., User]:
    def role_dependency(user: User = Depends(get_current_user)) -> User:
        if user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to perform this action.",
            )
        return user

    return role_dependency
