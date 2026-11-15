from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models.all_models import ModelVersion, Prediction
from app.services.classifier import load_model_bundle, predict_many
from app.services.crypto import crypto_service
from app.core.errors import AppException

def get_active_model(db: Session, model_id: Optional[str] = None) -> ModelVersion:
    if model_id:
        mv = db.query(ModelVersion).filter(ModelVersion.id == model_id).first()
        if not mv:
            raise AppException(404, "MODEL_NOT_FOUND", f"Model {model_id} not found")
        if mv.status not in ["deployed", "trained"]:
            raise AppException(400, "MODEL_NOT_READY", f"Model status is {mv.status}")
        return mv
    
    mv = db.query(ModelVersion).filter(ModelVersion.status == "deployed").order_by(ModelVersion.created_at.desc()).first()
    if not mv:
        mv = db.query(ModelVersion).filter(ModelVersion.status == "trained").order_by(ModelVersion.created_at.desc()).first()
    if not mv:
        raise AppException(400, "NO_DEPLOYED_MODEL", "No model is currently deployed or trained")
    return mv

def predict_and_store(
    db: Session,
    texts: List[str],
    model_id: Optional[str] = None,
    user_id: Optional[str] = None,
    document_ids: Optional[List[str]] = None
) -> List[Dict[str, Any]]:
    mv = get_active_model(db, model_id)
    bundle = load_model_bundle(mv.artifact_path)
    predictions = predict_many(bundle, texts)
    
    stored_results = []
    for i, pred in enumerate(predictions):
        doc_id = document_ids[i] if document_ids and i < len(document_ids) else None
        encrypted_input = crypto_service.encrypt(pred["text"])
        
        pred_record = Prediction(
            model_version_id=mv.id,
            document_id=doc_id,
            input_text_encrypted=encrypted_input,
            predicted_label=pred["predicted_label"],
            confidence=pred["confidence"],
            probabilities=pred["probabilities"],
            created_by=user_id
        )
        db.add(pred_record)
        db.flush()
        
        pred_dict = pred.copy()
        pred_dict["id"] = pred_record.id
        stored_results.append(pred_dict)
        
    db.commit()
    return stored_results
