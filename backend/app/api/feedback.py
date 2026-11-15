from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from app.db import get_db
from app.core.deps import get_current_user, record_audit_log
from app.core.rbac import require_roles
from app.core.errors import AppException
from app.models.all_models import User, Prediction, Feedback, Document
from app.schemas.all_schemas import FeedbackCreate, FeedbackResponse
from app.services.crypto import crypto_service
from app.config import settings

router = APIRouter(tags=["feedback"])

@router.get("/predictions")
def list_predictions_for_review(
    low_confidence_only: bool = Query(False),
    limit: int = 50,
    skip: int = 0,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Prediction)
    if low_confidence_only:
        query = query.filter(Prediction.confidence < settings.CONFIDENCE_THRESHOLD)
    
    predictions = query.order_by(Prediction.created_at.desc()).offset(skip).limit(limit).all()
    results = []
    for p in predictions:
        txt = crypto_service.decrypt(p.input_text_encrypted)
        results.append({
            "id": p.id,
            "text": txt,
            "predicted_label": p.predicted_label,
            "confidence": round(p.confidence, 4),
            "probabilities": p.probabilities,
            "created_at": p.created_at,
            "has_feedback": len(p.feedbacks) > 0
        })
    return results

@router.post("/feedback", response_model=FeedbackResponse, status_code=status.HTTP_201_CREATED)
def submit_feedback(
    payload: FeedbackCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("reviewer", "analyst", "data_scientist"))
):
    pred = db.query(Prediction).filter(Prediction.id == payload.prediction_id).first()
    if not pred:
        raise AppException(status.HTTP_404_NOT_FOUND, "PREDICTION_NOT_FOUND", "Prediction not found")

    fb = Feedback(
        prediction_id=pred.id,
        corrected_label=payload.corrected_label,
        comment=payload.comment,
        reviewer_id=current_user.id,
        status=payload.status
    )
    db.add(fb)

    if pred.document_id:
        doc = db.query(Document).filter(Document.id == pred.document_id).first()
        if doc:
            doc.label = payload.corrected_label

    db.commit()
    db.refresh(fb)

    record_audit_log(db, current_user.id, "SUBMIT_FEEDBACK", {
        "prediction_id": pred.id,
        "corrected_label": payload.corrected_label
    })

    return fb

@router.get("/feedback", response_model=List[FeedbackResponse])
def list_feedbacks(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return db.query(Feedback).order_by(Feedback.created_at.desc()).offset(skip).limit(limit).all()
