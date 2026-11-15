from typing import Optional
from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.db import get_db
from app.core.security import decode_access_token, hash_api_key
from app.core.errors import AppException
from app.models.all_models import User, ApiKey, AuditLog

security_scheme = HTTPBearer(auto_error=False)

def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
    db: Session = Depends(get_db)
) -> User:
    if not credentials:
        raise AppException(status.HTTP_401_UNAUTHORIZED, "UNAUTHORIZED", "Not authenticated")
    payload = decode_access_token(credentials.credentials)
    user_id: str = payload.get("sub")
    if not user_id:
        raise AppException(status.HTTP_401_UNAUTHORIZED, "INVALID_TOKEN", "Token missing subject")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise AppException(status.HTTP_404_NOT_FOUND, "USER_NOT_FOUND", "User not found")
    if not user.is_active:
        raise AppException(status.HTTP_403_FORBIDDEN, "INACTIVE_USER", "User is inactive")
    return user

def get_current_user_or_api_key(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
    db: Session = Depends(get_db)
) -> Optional[User]:
    if credentials:
        payload = decode_access_token(credentials.credentials)
        user_id: str = payload.get("sub")
        if user_id:
            user = db.query(User).filter(User.id == user_id).first()
            if user and user.is_active:
                return user
    if x_api_key:
        hashed = hash_api_key(x_api_key)
        api_key_obj = db.query(ApiKey).filter(ApiKey.key_hash == hashed).first()
        if api_key_obj:
            user = db.query(User).filter(User.id == api_key_obj.user_id).first()
            if user and user.is_active:
                return user
            return User(id=api_key_obj.user_id, email="external@source.api", name="External API Source", role="external_source", is_active=True)
    raise AppException(status.HTTP_401_UNAUTHORIZED, "UNAUTHORIZED", "Authentication required via Bearer token or X-API-Key")

def record_audit_log(db: Session, user_id: Optional[str], action: str, detail: dict) -> AuditLog:
    log_entry = AuditLog(
        user_id=user_id,
        action=action,
        detail=detail
    )
    db.add(log_entry)
    db.commit()
    db.refresh(log_entry)
    return log_entry
