from typing import List, Optional
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.db import get_db
from app.core.deps import get_current_user_or_api_key, get_current_user, record_audit_log
from app.core.errors import AppException
from app.models.all_models import User, Prediction
from app.schemas.all_schemas import (
    SinglePredictRequest,
    BatchPredictRequest,
    PredictionResult,
    TrendRequest,
    TrendResponse
)
from app.services.predictor import predict_and_store
from app.services.trends import compute_trend_forecast
from app.services.crypto import crypto_service

router = APIRouter(prefix="/predict", tags=["predict"])

@router.post("", response_model=List[PredictionResult])
def predict_endpoint(
    payload: SinglePredictRequest,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_or_api_key)
):
    if not payload.text or not payload.text.strip():
        raise AppException(status.HTTP_400_BAD_REQUEST, "EMPTY_INPUT", "Input text cannot be empty")
    
    user_id = current_user.id if current_user else None
    results = predict_and_store(
        db=db,
        texts=[payload.text],
        model_id=payload.model_id,
        user_id=user_id
    )
    return results

@router.post("/batch", response_model=List[PredictionResult])
def batch_predict_endpoint(
    payload: BatchPredictRequest,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_or_api_key)
):
    if not payload.texts:
        raise AppException(status.HTTP_400_BAD_REQUEST, "EMPTY_INPUT", "Texts list cannot be empty")
    
    user_id = current_user.id if current_user else None
    results = predict_and_store(
        db=db,
        texts=payload.texts,
        model_id=payload.model_id,
        user_id=user_id
    )
    return results

@router.post("/trend", response_model=TrendResponse)
def predict_trend(
    payload: TrendRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    trend_data = compute_trend_forecast(
        db=db,
        dataset_id=payload.dataset_id,
        target=payload.target,
        periods=payload.periods,
        period_type=payload.period_type
    )
    return trend_data
