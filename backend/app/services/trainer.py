import os
from typing import List, Dict, Any, Optional
import joblib
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from xgboost import XGBClassifier
from app.config import settings
from app.services.preprocess import clean_text
from app.services.semantic import get_text_embeddings
from app.services.evaluator import evaluate_predictions
from app.db import SessionLocal
from app.models.all_models import ModelVersion

def train_model_sync(
    model_version_id: str,
    texts: List[str],
    labels: List[str],
    algorithm: str,
    feature_type: str,
    test_split: float = 0.2
):
    db = SessionLocal()
    mv = db.query(ModelVersion).filter(ModelVersion.id == model_version_id).first()
    if not mv:
        db.close()
        return

    try:
        mv.status = "training"
        db.commit()

        cleaned_texts = [clean_text(t) if clean_text(t) else "sample" for t in texts]
        
        all_unique_labels = sorted(list(set(labels)))

        try:
            X_train_raw, X_test_raw, y_train_labels, y_test_labels = train_test_split(
                cleaned_texts, labels, test_size=test_split, random_state=42, stratify=labels
            )
        except ValueError:
            seen = set()
            train_idx, test_idx = [], []
            for i, l in enumerate(labels):
                if l not in seen:
                    seen.add(l)
                    train_idx.append(i)
                else:
                    test_idx.append(i)
            if not test_idx:
                test_idx = list(range(len(labels)))
                train_idx = list(range(len(labels)))
            X_train_raw = [cleaned_texts[i] for i in train_idx]
            y_train_labels = [labels[i] for i in train_idx]
            X_test_raw = [cleaned_texts[i] for i in test_idx]
            y_test_labels = [labels[i] for i in test_idx]

        train_label_encoder = LabelEncoder()
        y_train = train_label_encoder.fit_transform(y_train_labels)
        model_classes = train_label_encoder.classes_.tolist()

        vectorizer = None
        if "BERT" in feature_type.upper():
            X_train = get_text_embeddings(X_train_raw)
            X_test = get_text_embeddings(X_test_raw)
        else:
            vectorizer = TfidfVectorizer(max_features=5000, stop_words="english", ngram_range=(1, 2))
            X_train = vectorizer.fit_transform(X_train_raw)
            X_test = vectorizer.transform(X_test_raw)

        norm_alg = algorithm.lower().replace(" ", "").replace("_", "")
        if "xgboost" in norm_alg or "xgb" in norm_alg:
            clf = XGBClassifier(
                n_estimators=100,
                learning_rate=0.1,
                max_depth=5,
                random_state=42,
                eval_metric="mlogloss"
            )
        elif "randomforest" in norm_alg:
            clf = RandomForestClassifier(n_estimators=100, random_state=42)
        else:
            clf = LogisticRegression(max_iter=1000, random_state=42)

        clf.fit(X_train, y_train)

        y_pred_idx = clf.predict(X_test)
        y_pred_labels = [model_classes[idx] for idx in y_pred_idx]

        eval_classes = all_unique_labels
        metrics = evaluate_predictions(y_test_labels, y_pred_labels, eval_classes)

        os.makedirs(settings.MODEL_STORAGE_DIR, exist_ok=True)
        artifact_path = os.path.join(settings.MODEL_STORAGE_DIR, f"{model_version_id}.joblib")
        bundle = {
            "model": clf,
            "feature_type": feature_type,
            "vectorizer": vectorizer,
            "labels": model_classes,
            "algorithm": algorithm
        }
        joblib.dump(bundle, artifact_path)

        mv.artifact_path = artifact_path
        mv.metrics = metrics
        mv.status = "trained"
        db.commit()

    except Exception as e:
        mv.status = "failed"
        mv.metrics = {"error": str(e)}
        db.commit()
    finally:
        db.close()
