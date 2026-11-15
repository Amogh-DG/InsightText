import os
import csv
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(__file__))

from app.db import SessionLocal, engine, Base
from app.models.all_models import (
    User,
    ApiKey,
    Dataset,
    Document,
    ModelVersion,
    Prediction,
    Feedback,
    SystemSetting,
    AuditLog
)
from app.core.security import get_password_hash, hash_api_key
from app.services.crypto import crypto_service
from app.services.trainer import train_model_sync
from app.api.analysis import run_dataset_analysis_task
from app.config import settings

def seed():
    Base.metadata.create_all(bind=engine)
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
        existing = db.query(User).filter(User.email == u["email"]).first()
        if not existing:
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
        else:
            user_map[u["role"]] = existing

    admin_user = user_map.get("admin")

    raw_api_key = "ak_demo_external_key_12345678"
    existing_key = db.query(ApiKey).filter(ApiKey.label == "Default Ingest Key").first()
    if not existing_key and admin_user:
        api_key_obj = ApiKey(
            user_id=admin_user.id,
            key_hash=hash_api_key(raw_api_key),
            label="Default Ingest Key"
        )
        db.add(api_key_obj)
        db.commit()

    th_setting = db.query(SystemSetting).filter(SystemSetting.key == "confidence_threshold").first()
    if not th_setting:
        db.add(SystemSetting(key="confidence_threshold", value=0.6))
    
    intent_setting = db.query(SystemSetting).filter(SystemSetting.key == "intent_labels").first()
    if not intent_setting:
        db.add(SystemSetting(key="intent_labels", value=settings.INTENT_LABELS))
    db.commit()

    sample_csv = os.path.join(settings.STORAGE_DIR, "datasets", "support_tickets_q3.csv")
    if not os.path.exists(sample_csv):
        from generate_data import generate_sample_dataset
        generate_sample_dataset(sample_csv, 500)

    existing_ds = db.query(Dataset).filter(Dataset.name == "Support tickets Q3").first()
    if not existing_ds:
        rows = []
        with open(sample_csv, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        dataset = Dataset(
            name="Support tickets Q3",
            owner_id=admin_user.id if admin_user else None,
            source="upload",
            row_count=len(rows),
            text_column="feedback_text",
            label_column="category",
            time_column="created_at",
            status="ready"
        )
        db.add(dataset)
        db.commit()
        db.refresh(dataset)

        doc_objects = []
        for r in rows:
            dt = None
            if r.get("created_at"):
                try:
                    dt = datetime.strptime(r["created_at"], "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    pass
            doc = Document(
                dataset_id=dataset.id,
                text_encrypted=crypto_service.encrypt(r["feedback_text"]),
                label=r.get("category"),
                timestamp=dt,
                meta={},
                processed=False
            )
            doc_objects.append(doc)
        db.bulk_save_objects(doc_objects)
        db.commit()

        run_dataset_analysis_task(dataset.id, ["sentiment", "entities", "intent", "topics"], num_topics=4)

        texts = [r["feedback_text"] for r in rows]
        labels = [r["category"] for r in rows]

        mv = ModelVersion(
            name="Ticket Classifier",
            algorithm="XGBoost",
            feature_type="TF-IDF",
            dataset_id=dataset.id,
            version="v1.4",
            artifact_path="",
            metrics={},
            status="training",
            created_by=admin_user.id if admin_user else None
        )
        db.add(mv)
        db.commit()
        db.refresh(mv)

        train_model_sync(
            model_version_id=mv.id,
            texts=texts,
            labels=labels,
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
            created_by=admin_user.id if admin_user else None
        )
        db.add(mv2)

        mv3 = ModelVersion(
            name="Ticket Classifier",
            algorithm="Random Forest",
            feature_type="TF-IDF",
            dataset_id=dataset.id,
            version="v1.3",
            artifact_path=mv.artifact_path,
            metrics={"f1": 0.82, "accuracy": 0.83, "precision": 0.82, "recall": 0.81, "target_f1_met": False},
            status="archived",
            created_by=admin_user.id if admin_user else None
        )
        db.add(mv3)
        db.commit()

        sample_preds = [
            ("Delivery was late but the driver was kind", "Delivery", 0.54, {"Delivery": 0.54, "Support": 0.26, "Product quality": 0.12, "Billing": 0.08}),
            ("Charged twice, app also froze", "Billing", 0.58, {"Billing": 0.58, "Product quality": 0.28, "Delivery": 0.08, "Support": 0.06}),
            ("Not sure if I love the new layout", "Product quality", 0.61, {"Product quality": 0.61, "Support": 0.21, "Billing": 0.10, "Delivery": 0.08}),
            ("Package arrived late and the box was crushed.", "Delivery", 0.89, {"Delivery": 0.89, "Product quality": 0.07, "Billing": 0.03, "Support": 0.01})
        ]

        for text_p, label_p, conf_p, probs_p in sample_preds:
            p_obj = Prediction(
                model_version_id=mv.id,
                input_text_encrypted=crypto_service.encrypt(text_p),
                predicted_label=label_p,
                confidence=conf_p,
                probabilities=probs_p,
                created_by=admin_user.id if admin_user else None
            )
            db.add(p_obj)
        db.commit()

    db.close()

if __name__ == "__main__":
    seed()
