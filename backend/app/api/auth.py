import secrets
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.db import get_db
from app.core.security import verify_password, create_access_token, hash_api_key
from app.core.deps import get_current_user, record_audit_log
from app.core.errors import AppException
from app.models.all_models import User, ApiKey
from app.schemas.all_schemas import (
    LoginRequest,
    TokenResponse,
    UserResponse,
    ApiKeyCreate,
    ApiKeyResponse
)

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise AppException(
            status.HTTP_401_UNAUTHORIZED,
            "INVALID_CREDENTIALS",
            "Incorrect email or password. Try again or reset your password."
        )
    if not user.is_active:
        raise AppException(status.HTTP_403_FORBIDDEN, "INACTIVE_ACCOUNT", "Account is deactivated")

    access_token = create_access_token(data={"sub": user.id, "role": user.role, "email": user.email})
    record_audit_log(db, user.id, "LOGIN", {"email": user.email})
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user
    }

@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user

@router.post("/api-keys", response_model=ApiKeyResponse)
def create_api_key(
    payload: ApiKeyCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    raw_key = f"ak_{secrets.token_hex(24)}"
    key_hash = hash_api_key(raw_key)
    api_key = ApiKey(
        user_id=current_user.id,
        key_hash=key_hash,
        label=payload.label
    )
    db.add(api_key)
    db.commit()
    db.refresh(api_key)
    record_audit_log(db, current_user.id, "CREATE_API_KEY", {"key_id": api_key.id, "label": payload.label})
    return {
        "id": api_key.id,
        "label": api_key.label,
        "api_key": raw_key,
        "created_at": api_key.created_at
    }

@router.get("/api-keys", response_model=list[ApiKeyResponse])
def list_api_keys(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return db.query(ApiKey).filter(ApiKey.user_id == current_user.id).all()
