import os
import sys
import tempfile
import shutil
from datetime import datetime, timedelta
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine

backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

test_dir = tempfile.mkdtemp(prefix="insighttext_test_")
test_storage = os.path.join(test_dir, "storage")
test_models_dir = os.path.join(test_storage, "models")
test_datasets_dir = os.path.join(test_storage, "datasets")
os.makedirs(test_models_dir, exist_ok=True)
os.makedirs(test_datasets_dir, exist_ok=True)

test_db_path = os.path.join(test_storage, "test.db")
normalized_db_path = test_db_path.replace("\\", "/")
test_db_url = f"sqlite:///{normalized_db_path}"

from app.config import settings
settings.STORAGE_DIR = test_storage
settings.MODEL_STORAGE_DIR = test_models_dir
settings.DATASET_STORAGE_DIR = test_datasets_dir
settings.DATABASE_URL = test_db_url

import app.db as db_module
db_module.engine = create_engine(test_db_url, connect_args={"check_same_thread": False}, pool_pre_ping=True)
db_module.SessionLocal.configure(bind=db_module.engine)

from app.main import app
from app.db import SessionLocal
from app.models.all_models import (
    Base,
    User,
    ApiKey,
    Dataset,
    Document,
    Analysis,
    ModelVersion,
    Prediction,
    Feedback,
    SystemSetting
)
from app.core.security import get_password_hash, hash_api_key, create_access_token
from app.services.crypto import crypto_service
from app.services.trainer import train_model_sync

Base.metadata.create_all(bind=db_module.engine)

def _init_test_db():
    db = SessionLocal()
    users_data = [
        {"email": "priya.nair@northwind.io", "name": "Priya Nair", "password": "Password123!", "role": "admin"},
        {"email": "admin@example.com", "name": "System Admin", "password": "Admin123!", "role": "admin"},
        {"email": "analyst@example.com", "name": "Ana Costa", "password": "Analyst123!", "role": "analyst"},
        {"email": "scientist@example.com", "name": "Dan Scientist", "password": "Scientist123!", "role": "data_scientist"},
        {"email": "manager@example.com", "name": "Lena Fischer", "password": "Manager123!", "role": "manager"},
        {"email": "reviewer@example.com", "name": "Sam Reviewer", "password": "Reviewer123!", "role": "reviewer"},
    ]
    user_map = {}
    for u in users_data:
        user = User(
            email=u["email"],
            name=u["name"],
            password_hash=get_password_hash(u["password"]),
            role=u["role"],
            is_active=True
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        user_map[u["role"]] = user

    admin_user = user_map.get("admin")
    api_key_obj = ApiKey(
        user_id=admin_user.id,
        key_hash=hash_api_key("ak_demo_external_key_12345678"),
        label="Default Ingest Key"
    )
    db.add(api_key_obj)
    db.add(SystemSetting(key="confidence_threshold", value=0.6))
    db.add(SystemSetting(key="intent_labels", value=settings.INTENT_LABELS))
    db.commit()

    now = datetime.now()
    sample_rows = [
        ("Delivery was late but driver was kind", "Delivery", now - timedelta(days=2)),
        ("Package arrived on time in good shape", "Delivery", now - timedelta(days=3)),
        ("Driver could not find my address", "Delivery", now - timedelta(days=4)),
        ("Box was completely crushed on arrival", "Delivery", now - timedelta(days=5)),
        ("Charged twice on my credit card", "Billing", now - timedelta(days=6)),
        ("Invoice total does not match checkout", "Billing", now - timedelta(days=7)),
        ("Refund has not appeared on my bank statement", "Billing", now - timedelta(days=8)),
        ("Subscription renewed unexpectedly", "Billing", now - timedelta(days=9)),
        ("App crashed when opening camera", "Product quality", now - timedelta(days=10)),
        ("Search filter does not return relevant results", "Product quality", now - timedelta(days=11)),
        ("Buttons are too small on mobile screen", "Product quality", now - timedelta(days=12)),
        ("Battery drain is significant with latest update", "Product quality", now - timedelta(days=13)),
        ("Agent was helpful and resolved my query", "Support", now - timedelta(days=14)),
        ("Waited forty minutes on hold without answer", "Support", now - timedelta(days=15)),
        ("Chatbot gave wrong answer to cancellation policy", "Support", now - timedelta(days=16)),
        ("Customer service ticket closed without resolution", "Support", now - timedelta(days=17)),
        ("Delivery delayed by a week without notice", "Delivery", now - timedelta(days=18)),
        ("Overcharged on shipping fee", "Billing", now - timedelta(days=19)),
        ("Audio playback has stuttering issues", "Product quality", now - timedelta(days=20)),
        ("Great customer service response time", "Support", now - timedelta(days=21)),
    ]

    dataset = Dataset(
        name="Support tickets Q3",
        owner_id=admin_user.id,
        source="upload",
        row_count=len(sample_rows),
        text_column="feedback_text",
        label_column="category",
        time_column="created_at",
        status="ready"
    )
    db.add(dataset)
    db.commit()
    db.refresh(dataset)

    doc_objs = []
    for idx, (txt, lbl, dt) in enumerate(sample_rows):
        doc = Document(
            dataset_id=dataset.id,
            text_encrypted=crypto_service.encrypt(txt),
            label=lbl,
            timestamp=dt,
            meta={"index": idx},
            processed=True
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)
        doc_objs.append(doc)

        analysis = Analysis(
            document_id=doc.id,
            sentiment_label="negative" if any(w in txt.lower() for w in ["crushed", "twice", "crashed", "delayed"]) else "positive",
            sentiment_score=0.92,
            entities=[{"text": lbl.lower(), "label": "CATEGORY"}],
            intent="complaint" if any(w in txt.lower() for w in ["twice", "crashed"]) else "inquiry",
            intent_score=0.88,
            topic_id=str(idx % 4),
            low_confidence=False
        )
        db.add(analysis)
    db.commit()

    mv = ModelVersion(
        name="Ticket Classifier",
        algorithm="XGBoost",
        feature_type="TF-IDF",
        dataset_id=dataset.id,
        version="v1.4",
        artifact_path="",
        metrics={"f1": 0.88, "accuracy": 0.90, "precision": 0.89, "recall": 0.87, "target_f1_met": True},
        status="training",
        created_by=admin_user.id
    )
    db.add(mv)
    db.commit()
    db.refresh(mv)

    train_model_sync(
        model_version_id=mv.id,
        texts=[r[0] for r in sample_rows],
        labels=[r[1] for r in sample_rows],
        algorithm="XGBoost",
        feature_type="TF-IDF",
        test_split=0.2
    )
    mv.status = "deployed"
    db.commit()

    mv2 = ModelVersion(
        name="Ticket Classifier",
        algorithm="Logistic Regression",
        feature_type="TF-IDF",
        dataset_id=dataset.id,
        version="v1.2",
        artifact_path=mv.artifact_path,
        metrics={"f1": 0.78, "accuracy": 0.80, "precision": 0.79, "recall": 0.77, "target_f1_met": False},
        status="archived",
        created_by=admin_user.id
    )
    db.add(mv2)
    db.commit()

    sample_preds = [
        ("Delivery was late but driver was kind", "Delivery", 0.54, {"Delivery": 0.54, "Support": 0.26, "Product quality": 0.12, "Billing": 0.08}, doc_objs[0].id),
        ("Charged twice, app also froze", "Billing", 0.58, {"Billing": 0.58, "Product quality": 0.28, "Delivery": 0.08, "Support": 0.06}, doc_objs[4].id),
        ("Not sure if I love new layout", "Product quality", 0.61, {"Product quality": 0.61, "Support": 0.21, "Billing": 0.10, "Delivery": 0.08}, None),
    ]
    for text_p, label_p, conf_p, probs_p, d_id in sample_preds:
        p_obj = Prediction(
            model_version_id=mv.id,
            document_id=d_id,
            input_text_encrypted=crypto_service.encrypt(text_p),
            predicted_label=label_p,
            confidence=conf_p,
            probabilities=probs_p,
            created_by=admin_user.id
        )
        db.add(p_obj)
    db.commit()

    fb_user = user_map.get("reviewer")
    pred_first = db.query(Prediction).first()
    if pred_first and fb_user:
        fb = Feedback(
            prediction_id=pred_first.id,
            corrected_label="Delivery",
            comment="Confirmed by agent",
            reviewer_id=fb_user.id,
            status="approved"
        )
        db.add(fb)
        db.commit()

    db.close()

_init_test_db()

@pytest.fixture(scope="session", autouse=True)
def teardown_test_environment():
    yield
    db_module.engine.dispose()
    shutil.rmtree(test_dir, ignore_errors=True)

@pytest.fixture(scope="session")
def client():
    with TestClient(app) as test_client:
        yield test_client

@pytest.fixture(scope="session")
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@pytest.fixture(scope="session")
def auth_headers(db_session):
    def _get_headers(role: str):
        user = db_session.query(User).filter(User.role == role).first()
        if not user:
            user = db_session.query(User).filter(User.email.contains(role)).first()
        token = create_access_token(data={"sub": user.id, "role": user.role, "email": user.email})
        return {"Authorization": f"Bearer {token}"}
    return _get_headers

@pytest.fixture(scope="session")
def admin_headers(auth_headers):
    return auth_headers("admin")

@pytest.fixture(scope="session")
def analyst_headers(auth_headers):
    return auth_headers("analyst")

@pytest.fixture(scope="session")
def scientist_headers(auth_headers):
    return auth_headers("data_scientist")

@pytest.fixture(scope="session")
def manager_headers(auth_headers):
    return auth_headers("manager")

@pytest.fixture(scope="session")
def reviewer_headers(auth_headers):
    return auth_headers("reviewer")

@pytest.fixture(scope="session")
def api_key_headers():
    return {"X-API-Key": "ak_demo_external_key_12345678"}
