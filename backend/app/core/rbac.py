from typing import Sequence
from fastapi import Depends, status
from app.core.deps import get_current_user
from app.core.errors import AppException
from app.models.all_models import User

def require_roles(*roles: str):
    allowed = set(roles)
    def role_dependency(user: User = Depends(get_current_user)) -> User:
        if user.role == "admin":
            return user
        if user.role not in allowed:
            raise AppException(
                status.HTTP_403_FORBIDDEN,
                "FORBIDDEN",
                f"Action requires one of the roles: {', '.join(allowed)}"
            )
        return user
    return role_dependency
