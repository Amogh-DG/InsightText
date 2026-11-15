from datetime import datetime
from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, EmailStr, Field, ConfigDict

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: "UserResponse"

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class UserCreate(BaseModel):
    email: EmailStr
    name: str
    password: str
    role: str = "analyst"

class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None
    password: Optional[str] = None

class UserResponse(BaseModel):
    id: str
    email: str
    name: str
    role: str
    is_active: bool
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class ApiKeyCreate(BaseModel):
    label: str

class ApiKeyResponse(BaseModel):
    id: str
    label: str
    api_key: Optional[str] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class DatasetResponse(BaseModel):
    id: str
    owner_id: Optional[str]
    name: str
    source: str
    row_count: int
    text_column: str
    label_column: Optional[str]
    time_column: Optional[str]
    status: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class PreviewRow(BaseModel):
    index: int
    data: Dict[str, Any]

class DatasetPreviewResponse(BaseModel):
    columns: List[str]
    rows: List[Dict[str, Any]]
    total_rows: int

class IngestPayload(BaseModel):
    name: Optional[str] = "API Ingest"
    text_column: str = "text"
    label_column: Optional[str] = None
    time_column: Optional[str] = None
    records: List[Dict[str, Any]]

class AnalysisRunRequest(BaseModel):
    dataset_id: str
    analysis_types: List[str] = Field(default_factory=lambda: ["sentiment", "entities", "intent", "topics"])
    num_topics: Optional[int] = 6

class EntityItem(BaseModel):
    text: str
    label: str

class SemanticTextRequest(BaseModel):
    text: str

class SemanticTextResponse(BaseModel):
    text: str
    sentiment_label: str
    sentiment_score: float
    entities: List[EntityItem]
    intent: str
    intent_score: float
    low_confidence: bool

class AnalysisItemResponse(BaseModel):
    id: str
    document_id: str
    text: str
    sentiment_label: str
    sentiment_score: float
    entities: List[EntityItem]
    intent: str
    intent_score: float
    topic_id: Optional[str]
    low_confidence: bool
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class TopicResponse(BaseModel):
    id: str
    dataset_id: str
    keywords: List[str]
    size: int
    model_config = ConfigDict(from_attributes=True)

class TrainModelRequest(BaseModel):
    dataset_id: str
    algorithm: str = "XGBoost"
    feature_type: str = "TF-IDF"
    test_split: float = 0.2
    name: Optional[str] = None

class PerClassMetric(BaseModel):
    precision: float
    recall: float
    f1: float
    support: int

class ModelVersionResponse(BaseModel):
    id: str
    name: str
    algorithm: str
    feature_type: str
    dataset_id: Optional[str]
    version: str
    metrics: Dict[str, Any]
    status: str
    created_by: Optional[str]
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class ModelUpdate(BaseModel):
    name: Optional[str] = None
    status: Optional[str] = None

class ConfusionMatrixData(BaseModel):
    labels: List[str]
    matrix: List[List[int]]

class ModelEvaluationResponse(BaseModel):
    model_id: str
    accuracy: float
    precision: float
    recall: float
    f1: float
    target_f1_met: bool
    per_class_report: Dict[str, PerClassMetric]
    confusion_matrix: ConfusionMatrixData

class SinglePredictRequest(BaseModel):
    model_id: Optional[str] = None
    text: str

class BatchPredictRequest(BaseModel):
    model_id: Optional[str] = None
    texts: List[str]

class PredictionResult(BaseModel):
    id: Optional[str] = None
    text: str
    predicted_label: str
    confidence: float
    probabilities: Dict[str, float]

class TrendRequest(BaseModel):
    dataset_id: Optional[str] = None
    target: str = "sentiment"
    periods: int = 7
    period_type: str = "day"

class TrendPoint(BaseModel):
    date: str
    actual: Optional[float] = None
    forecast: Optional[float] = None
    is_forecast: bool = False

class TrendResponse(BaseModel):
    target: str
    points: List[TrendPoint]
    summary_change_pct: float
    summary_text: str

class FeedbackCreate(BaseModel):
    prediction_id: str
    corrected_label: str
    comment: Optional[str] = None
    status: str = "submitted"

class FeedbackResponse(BaseModel):
    id: str
    prediction_id: str
    corrected_label: str
    comment: Optional[str]
    reviewer_id: Optional[str]
    status: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class DashboardSummary(BaseModel):
    documents_processed: int
    datasets_count: int
    deployed_model_f1: Optional[float]
    deployed_model_name: Optional[str]
    predictions_today: int
    sentiment_distribution: Dict[str, float]
    label_distribution: Dict[str, float]
    topic_sizes: List[Dict[str, Any]]
    recent_low_confidence: List[Dict[str, Any]]
    trend_points: List[TrendPoint]

class SettingUpdate(BaseModel):
    confidence_threshold: Optional[float] = None
    intent_labels: Optional[List[str]] = None

class SettingResponse(BaseModel):
    confidence_threshold: float
    intent_labels: List[str]
    target_f1: float
