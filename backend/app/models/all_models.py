import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, Integer, Float, DateTime, ForeignKey, JSON, Text
from sqlalchemy.orm import relationship
from app.db import Base

class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(255), unique=True, index=True, nullable=False)
    name = Column(String(255), nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False, default="analyst")
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    datasets = relationship("Dataset", back_populates="owner", cascade="all, delete-orphan")
    api_keys = relationship("ApiKey", back_populates="user", cascade="all, delete-orphan")
    feedbacks = relationship("Feedback", back_populates="reviewer")
    audit_logs = relationship("AuditLog", back_populates="user")

class ApiKey(Base):
    __tablename__ = "api_keys"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    key_hash = Column(String(255), unique=True, index=True, nullable=False)
    label = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="api_keys")

class Dataset(Base):
    __tablename__ = "datasets"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    owner_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    name = Column(String(255), nullable=False)
    source = Column(String(50), nullable=False, default="upload")
    row_count = Column(Integer, default=0, nullable=False)
    text_column = Column(String(255), nullable=False)
    label_column = Column(String(255), nullable=True)
    time_column = Column(String(255), nullable=True)
    status = Column(String(50), default="ready", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    owner = relationship("User", back_populates="datasets")
    documents = relationship("Document", back_populates="dataset", cascade="all, delete-orphan")
    topics = relationship("Topic", back_populates="dataset", cascade="all, delete-orphan")
    models = relationship("ModelVersion", back_populates="dataset")

class Document(Base):
    __tablename__ = "documents"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    dataset_id = Column(String(36), ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False)
    text_encrypted = Column(Text, nullable=False)
    label = Column(String(255), nullable=True)
    timestamp = Column(DateTime, nullable=True)
    meta = Column(JSON, default=dict, nullable=False)
    processed = Column(Boolean, default=False, nullable=False)

    dataset = relationship("Dataset", back_populates="documents")
    analysis = relationship("Analysis", back_populates="document", uselist=False, cascade="all, delete-orphan")
    predictions = relationship("Prediction", back_populates="document")

class Topic(Base):
    __tablename__ = "topics"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    dataset_id = Column(String(36), ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False)
    keywords = Column(JSON, default=list, nullable=False)
    size = Column(Integer, default=0, nullable=False)

    dataset = relationship("Dataset", back_populates="topics")
    analyses = relationship("Analysis", back_populates="topic")

class Analysis(Base):
    __tablename__ = "analyses"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id = Column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    sentiment_label = Column(String(50), nullable=False)
    sentiment_score = Column(Float, nullable=False)
    entities = Column(JSON, default=list, nullable=False)
    intent = Column(String(100), nullable=False)
    intent_score = Column(Float, nullable=False)
    topic_id = Column(String(36), ForeignKey("topics.id", ondelete="SET NULL"), nullable=True)
    low_confidence = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    document = relationship("Document", back_populates="analysis")
    topic = relationship("Topic", back_populates="analyses")

class ModelVersion(Base):
    __tablename__ = "model_versions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    algorithm = Column(String(100), nullable=False)
    feature_type = Column(String(50), nullable=False)
    dataset_id = Column(String(36), ForeignKey("datasets.id", ondelete="SET NULL"), nullable=True)
    version = Column(String(50), nullable=False)
    artifact_path = Column(String(500), nullable=False)
    metrics = Column(JSON, default=dict, nullable=False)
    status = Column(String(50), default="trained", nullable=False)
    created_by = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    dataset = relationship("Dataset", back_populates="models")
    predictions = relationship("Prediction", back_populates="model_version")

class Prediction(Base):
    __tablename__ = "predictions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    model_version_id = Column(String(36), ForeignKey("model_versions.id", ondelete="SET NULL"), nullable=True)
    document_id = Column(String(36), ForeignKey("documents.id", ondelete="SET NULL"), nullable=True)
    input_text_encrypted = Column(Text, nullable=False)
    predicted_label = Column(String(255), nullable=False)
    confidence = Column(Float, nullable=False)
    probabilities = Column(JSON, default=dict, nullable=False)
    created_by = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    model_version = relationship("ModelVersion", back_populates="predictions")
    document = relationship("Document", back_populates="predictions")
    feedbacks = relationship("Feedback", back_populates="prediction", cascade="all, delete-orphan")

class Feedback(Base):
    __tablename__ = "feedbacks"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    prediction_id = Column(String(36), ForeignKey("predictions.id", ondelete="CASCADE"), nullable=False)
    corrected_label = Column(String(255), nullable=False)
    comment = Column(Text, nullable=True)
    reviewer_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    status = Column(String(50), default="submitted", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    prediction = relationship("Prediction", back_populates="feedbacks")
    reviewer = relationship("User", back_populates="feedbacks")

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    action = Column(String(255), nullable=False)
    detail = Column(JSON, default=dict, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="audit_logs")

class SystemSetting(Base):
    __tablename__ = "system_settings"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    key = Column(String(100), unique=True, index=True, nullable=False)
    value = Column(JSON, nullable=False)
