from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db import get_db
from app.core.deps import record_audit_log
from app.core.rbac import require_roles
from app.models.all_models import User, SystemSetting
from app.schemas.all_schemas import SettingUpdate, SettingResponse
from app.config import settings

router = APIRouter(prefix="/settings", tags=["settings"])

@router.get("", response_model=SettingResponse)
def get_system_settings(
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_roles("admin"))
):
    th_record = db.query(SystemSetting).filter(SystemSetting.key == "confidence_threshold").first()
    threshold = float(th_record.value) if th_record else settings.CONFIDENCE_THRESHOLD

    intent_record = db.query(SystemSetting).filter(SystemSetting.key == "intent_labels").first()
    intent_labels = intent_record.value if intent_record else settings.INTENT_LABELS

    return {
        "confidence_threshold": threshold,
        "intent_labels": intent_labels,
        "target_f1": settings.TARGET_F1
    }

@router.patch("", response_model=SettingResponse)
def update_system_settings(
    payload: SettingUpdate,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_roles("admin"))
):
    updates = {}
    if payload.confidence_threshold is not None:
        th_record = db.query(SystemSetting).filter(SystemSetting.key == "confidence_threshold").first()
        if not th_record:
            th_record = SystemSetting(key="confidence_threshold", value=payload.confidence_threshold)
            db.add(th_record)
        else:
            th_record.value = payload.confidence_threshold
        updates["confidence_threshold"] = payload.confidence_threshold

    if payload.intent_labels is not None:
        intent_record = db.query(SystemSetting).filter(SystemSetting.key == "intent_labels").first()
        if not intent_record:
            intent_record = SystemSetting(key="intent_labels", value=payload.intent_labels)
            db.add(intent_record)
        else:
            intent_record.value = payload.intent_labels
        updates["intent_labels"] = payload.intent_labels

    db.commit()
    record_audit_log(db, admin_user.id, "UPDATE_SETTINGS", updates)

    th_record = db.query(SystemSetting).filter(SystemSetting.key == "confidence_threshold").first()
    threshold = float(th_record.value) if th_record else settings.CONFIDENCE_THRESHOLD

    intent_record = db.query(SystemSetting).filter(SystemSetting.key == "intent_labels").first()
    intent_labels = intent_record.value if intent_record else settings.INTENT_LABELS

    return {
        "confidence_threshold": threshold,
        "intent_labels": intent_labels,
        "target_f1": settings.TARGET_F1
    }
