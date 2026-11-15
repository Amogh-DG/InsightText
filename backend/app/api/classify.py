from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.db import get_db
from app.core.deps import get_current_user, record_audit_log
from app.core.rbac import require_roles
from app.core.errors import AppException
from app.models.all_models import User, Dataset, Document
from app.services.predictor import predict_and_store, get_active_model
from app.services.crypto import crypto_service

router = APIRouter(prefix="/classify", tags=["classify"])

class ClassifyRequest(BaseModel):
    model_id: Optional[str] = None
    text: Optional[str] = None
    dataset_id: Optional[str] = None

class ClassifyResultItem(BaseModel):
    id: Optional[str] = None
    text: str
    predicted_label: str
    confidence: float
    probabilities: Dict[str, float]

@router.post("", response_model=List[ClassifyResultItem])
def classify(
    payload: ClassifyRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("analyst", "data_scientist"))
):
    if not payload.text and not payload.dataset_id:
        raise AppException(
            status.HTTP_400_BAD_REQUEST,
            "INVALID_INPUT",
            "Either 'text' or 'dataset_id' must be provided"
        )

    model = get_active_model(db, payload.model_id)

    if payload.text:
        texts = [payload.text]
        doc_ids = None
    else:
        dataset = db.query(Dataset).filter(Dataset.id == payload.dataset_id).first()
        if not dataset:
            raise AppException(status.HTTP_404_NOT_FOUND, "DATASET_NOT_FOUND", "Dataset not found")
        docs = db.query(Document).filter(Document.dataset_id == payload.dataset_id).limit(100).all()
        if not docs:
            return []
        texts = [crypto_service.decrypt(d.text_encrypted) for d in docs]
        doc_ids = [d.id for d in docs]

    results = predict_and_store(
        db=db,
        texts=texts,
        model_id=model.id,
        user_id=current_user.id,
        document_ids=doc_ids
    )

    record_audit_log(db, current_user.id, "CLASSIFY", {"model_id": model.id, "count": len(results)})
    return results
