from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.db import get_db
from app.core.security import get_password_hash
from app.core.rbac import require_roles
from app.core.deps import record_audit_log
from app.core.errors import AppException
from app.models.all_models import User
from app.schemas.all_schemas import UserCreate, UserUpdate, UserResponse

router = APIRouter(prefix="/users", tags=["users"])

@router.get("", response_model=List[UserResponse])
def list_users(
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_roles("admin"))
):
    return db.query(User).order_by(User.created_at.desc()).all()

@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    payload: UserCreate,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_roles("admin"))
):
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise AppException(status.HTTP_409_CONFLICT, "EMAIL_EXISTS", "A user with this email already exists")
    
    user = User(
        email=payload.email,
        name=payload.name,
        password_hash=get_password_hash(payload.password),
        role=payload.role,
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    record_audit_log(db, admin_user.id, "CREATE_USER", {"target_user_id": user.id, "email": user.email, "role": user.role})
    return user

@router.patch("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: str,
    payload: UserUpdate,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_roles("admin"))
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise AppException(status.HTTP_404_NOT_FOUND, "USER_NOT_FOUND", "User not found")
    
    updates = {}
    if payload.name is not None:
        user.name = payload.name
        updates["name"] = payload.name
    if payload.email is not None:
        conflict = db.query(User).filter(User.email == payload.email, User.id != user_id).first()
        if conflict:
            raise AppException(status.HTTP_409_CONFLICT, "EMAIL_EXISTS", "Email already in use")
        user.email = payload.email
        updates["email"] = payload.email
    if payload.role is not None:
        user.role = payload.role
        updates["role"] = payload.role
    if payload.is_active is not None:
        user.is_active = payload.is_active
        updates["is_active"] = payload.is_active
    if payload.password is not None:
        user.password_hash = get_password_hash(payload.password)
        updates["password_updated"] = True

    db.commit()
    db.refresh(user)
    record_audit_log(db, admin_user.id, "UPDATE_USER", {"target_user_id": user.id, "changes": updates})
    return user

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: str,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_roles("admin"))
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise AppException(status.HTTP_404_NOT_FOUND, "USER_NOT_FOUND", "User not found")
    db.delete(user)
    db.commit()
    record_audit_log(db, admin_user.id, "DELETE_USER", {"target_user_id": user_id})
    return None
