import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, BackgroundTasks, status
from sqlalchemy.orm import Session
from app.db import get_db
from app.core.deps import get_current_user, record_audit_log
from app.core.rbac import require_roles
from app.core.errors import AppException
from app.models.all_models import User, Prediction, Feedback, Document, Dataset, ModelVersion
from app.schemas.all_schemas import FeedbackCreate, FeedbackResponse
from app.services.crypto import crypto_service
from app.services.trainer import train_model_sync
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
    else:
        dataset = db.query(Dataset).filter(Dataset.name == "Accumulated Feedback").first()
        if not dataset:
            dataset = Dataset(
                name="Accumulated Feedback",
                owner_id=current_user.id,
                source="feedback",
                row_count=0,
                text_column="text",
                label_column="label",
                status="ready"
            )
            db.add(dataset)
            db.commit()
            db.refresh(dataset)

        new_doc = Document(
            dataset_id=dataset.id,
            text_encrypted=pred.input_text_encrypted,
            label=payload.corrected_label,
            meta={},
            processed=True
        )
        db.add(new_doc)
        db.commit()
        db.refresh(new_doc)
        
        pred.document_id = new_doc.id
        dataset.row_count = db.query(Document).filter(Document.dataset_id == dataset.id).count()

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

@router.post("/feedback/retrain", status_code=status.HTTP_202_ACCEPTED)
def retrain_from_feedback(
    background_tasks: BackgroundTasks,
    algorithm: str = "XGBoost",
    feature_type: str = "TF-IDF",
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("data_scientist", "admin"))
):
    dataset = db.query(Dataset).filter(Dataset.name == "Accumulated Feedback").first()
    if not dataset or db.query(Document).filter(Document.dataset_id == dataset.id, Document.label.isnot(None)).count() < 5:
        dataset = db.query(Dataset).filter(Dataset.label_column.isnot(None)).first()
        
    if not dataset:
        raise AppException(status.HTTP_400_BAD_REQUEST, "NO_DATASET", "No labeled dataset available for retraining")
        
    docs = db.query(Document).filter(Document.dataset_id == dataset.id, Document.label.isnot(None)).all()
    if len(docs) < 5:
        raise AppException(status.HTTP_400_BAD_REQUEST, "INSUFFICIENT_DATA", "Need at least 5 labeled examples to retrain")
        
    texts = [crypto_service.decrypt(d.text_encrypted) for d in docs]
    labels = [d.label for d in docs]
    
    existing_count = db.query(ModelVersion).count()
    ver_str = f"v{existing_count + 1}.0-feedback"
    
    mv = ModelVersion(
        id=str(uuid.uuid4()),
        name=f"Retrained-{dataset.name[:15]}",
        algorithm=algorithm,
        feature_type=feature_type,
        dataset_id=dataset.id,
        version=ver_str,
        status="training",
        progress_stage="queued",
        artifact_path="",
        metrics={},
        created_by=current_user.id
    )
    db.add(mv)
    db.commit()
    db.refresh(mv)
    
    background_tasks.add_task(
        train_model_sync,
        model_version_id=mv.id,
        texts=texts,
        labels=labels,
        algorithm=algorithm,
        feature_type=feature_type,
        test_split=0.2
    )
    
    record_audit_log(db, current_user.id, "RETRAIN_MODEL", {
        "model_version_id": mv.id,
        "dataset_id": dataset.id
    })
    
    return {
        "model_id": mv.id,
        "version": mv.version,
        "status": "training",
        "message": f"Retraining started with {len(texts)} feedback examples"
    }
