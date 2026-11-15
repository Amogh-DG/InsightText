import os
from typing import List, Optional
from fastapi import APIRouter, Depends, BackgroundTasks, status
from sqlalchemy.orm import Session
from app.db import get_db
from app.core.deps import get_current_user, record_audit_log
from app.core.rbac import require_roles
from app.core.errors import AppException
from app.models.all_models import User, Dataset, Document, ModelVersion
from app.schemas.all_schemas import (
    TrainModelRequest,
    ModelVersionResponse,
    ModelEvaluationResponse,
    ModelUpdate
)
from app.services.trainer import train_model_sync
from app.services.crypto import crypto_service
from app.services.classifier import clear_model_cache

router = APIRouter(prefix="/models", tags=["models"])

@router.post("/train", response_model=ModelVersionResponse, status_code=status.HTTP_202_ACCEPTED)
def train_model(
    payload: TrainModelRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("data_scientist"))
):
    dataset = db.query(Dataset).filter(Dataset.id == payload.dataset_id).first()
    if not dataset:
        raise AppException(status.HTTP_404_NOT_FOUND, "DATASET_NOT_FOUND", "Dataset not found")

    docs = db.query(Document).filter(Document.dataset_id == payload.dataset_id, Document.label.isnot(None)).all()
    if len(docs) < 5:
        raise AppException(
            status.HTTP_400_BAD_REQUEST,
            "INSUFFICIENT_LABELED_DATA",
            "Dataset must contain at least 5 labeled documents for training"
        )

    texts = [crypto_service.decrypt(d.text_encrypted) for d in docs]
    labels = [d.label for d in docs]

    count_existing = db.query(ModelVersion).filter(ModelVersion.dataset_id == payload.dataset_id).count()
    version_str = f"v1.{count_existing + 1}"

    model_name = payload.name or f"{dataset.name.replace(' ', '')}Classifier"
    
    mv = ModelVersion(
        name=model_name,
        algorithm=payload.algorithm,
        feature_type=payload.feature_type,
        dataset_id=dataset.id,
        version=version_str,
        artifact_path="",
        metrics={},
        status="training",
        created_by=current_user.id
    )
    db.add(mv)
    db.commit()
    db.refresh(mv)

    background_tasks.add_task(
        train_model_sync,
        mv.id,
        texts,
        labels,
        payload.algorithm,
        payload.feature_type,
        payload.test_split
    )

    record_audit_log(db, current_user.id, "TRAIN_MODEL", {
        "model_id": mv.id,
        "name": mv.name,
        "algorithm": mv.algorithm,
        "feature_type": mv.feature_type
    })

    return mv

@router.get("", response_model=List[ModelVersionResponse])
def list_models(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return db.query(ModelVersion).order_by(ModelVersion.created_at.desc()).all()

@router.get("/{model_id}", response_model=ModelVersionResponse)
def get_model(
    model_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    mv = db.query(ModelVersion).filter(ModelVersion.id == model_id).first()
    if not mv:
        raise AppException(status.HTTP_404_NOT_FOUND, "MODEL_NOT_FOUND", "Model not found")
    return mv

@router.post("/{model_id}/deploy", response_model=ModelVersionResponse)
def deploy_model(
    model_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("data_scientist"))
):
    mv = db.query(ModelVersion).filter(ModelVersion.id == model_id).first()
    if not mv:
        raise AppException(status.HTTP_404_NOT_FOUND, "MODEL_NOT_FOUND", "Model not found")
    if mv.status not in ["trained", "archived"]:
        raise AppException(status.HTTP_400_BAD_REQUEST, "INVALID_STATUS", f"Cannot deploy model with status '{mv.status}'")

    db.query(ModelVersion).filter(ModelVersion.status == "deployed").update({"status": "archived"})
    mv.status = "deployed"
    db.commit()
    db.refresh(mv)

    clear_model_cache()
    record_audit_log(db, current_user.id, "DEPLOY_MODEL", {"model_id": mv.id, "version": mv.version})
    return mv

@router.post("/{model_id}/evaluate", response_model=ModelEvaluationResponse)
def evaluate_model(
    model_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("data_scientist"))
):
    mv = db.query(ModelVersion).filter(ModelVersion.id == model_id).first()
    if not mv:
        raise AppException(status.HTTP_404_NOT_FOUND, "MODEL_NOT_FOUND", "Model not found")
    if not mv.metrics or "confusion_matrix" not in mv.metrics:
        raise AppException(status.HTTP_400_BAD_REQUEST, "NO_METRICS", "Model has not been evaluated yet")

    m = mv.metrics
    return {
        "model_id": mv.id,
        "accuracy": m.get("accuracy", 0.0),
        "precision": m.get("precision", 0.0),
        "recall": m.get("recall", 0.0),
        "f1": m.get("f1", 0.0),
        "target_f1_met": m.get("target_f1_met", False),
        "per_class_report": m.get("per_class_report", {}),
        "confusion_matrix": m.get("confusion_matrix", {"labels": [], "matrix": []})
    }

@router.patch("/{model_id}", response_model=ModelVersionResponse)
def update_model(
    model_id: str,
    payload: ModelUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("data_scientist"))
):
    mv = db.query(ModelVersion).filter(ModelVersion.id == model_id).first()
    if not mv:
        raise AppException(status.HTTP_404_NOT_FOUND, "MODEL_NOT_FOUND", "Model not found")
    
    if payload.status:
        if payload.status == "deployed":
            db.query(ModelVersion).filter(ModelVersion.status == "deployed", ModelVersion.id != model_id).update({"status": "archived"})
        mv.status = payload.status
    if payload.name:
        mv.name = payload.name

    db.commit()
    db.refresh(mv)
    clear_model_cache(mv.artifact_path)
    record_audit_log(db, current_user.id, "UPDATE_MODEL", {"model_id": mv.id, "status": mv.status})
    return mv

@router.delete("/{model_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_model(
    model_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("data_scientist"))
):
    mv = db.query(ModelVersion).filter(ModelVersion.id == model_id).first()
    if not mv:
        raise AppException(status.HTTP_404_NOT_FOUND, "MODEL_NOT_FOUND", "Model not found")
    
    if mv.artifact_path and os.path.exists(mv.artifact_path):
        try:
            os.remove(mv.artifact_path)
        except OSError:
            pass

    clear_model_cache(mv.artifact_path)
    db.delete(mv)
    db.commit()
    record_audit_log(db, current_user.id, "DELETE_MODEL", {"model_id": model_id})
    return None
