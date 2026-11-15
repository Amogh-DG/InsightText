from typing import Dict, Any, List
import os
import joblib
import numpy as np
from app.services.preprocess import clean_text
from app.services.semantic import get_text_embeddings

_model_cache: Dict[str, Dict[str, Any]] = {}

def load_model_bundle(artifact_path: str) -> Dict[str, Any]:
    if artifact_path in _model_cache:
        return _model_cache[artifact_path]
    if not os.path.exists(artifact_path):
        raise FileNotFoundError(f"Model artifact not found at {artifact_path}")
    bundle = joblib.load(artifact_path)
    _model_cache[artifact_path] = bundle
    return bundle

def clear_model_cache(artifact_path: str = None):
    if artifact_path:
        _model_cache.pop(artifact_path, None)
    else:
        _model_cache.clear()

def predict_single(bundle: Dict[str, Any], text: str) -> Dict[str, Any]:
    return predict_many(bundle, [text])[0]

def predict_many(bundle: Dict[str, Any], texts: List[str]) -> List[Dict[str, Any]]:
    cleaned_texts = [clean_text(t) if clean_text(t) else "empty" for t in texts]
    feature_type = bundle.get("feature_type", "TF-IDF").upper()
    model = bundle["model"]
    classes = bundle["labels"]
    
    if "BERT" in feature_type:
        X = get_text_embeddings(cleaned_texts)
    else:
        vectorizer = bundle["vectorizer"]
        X = vectorizer.transform(cleaned_texts)

    if hasattr(model, "predict_proba"):
        probabilities_matrix = model.predict_proba(X)
    else:
        decision = model.decision_function(X)
        exp_dec = np.exp(decision - np.max(decision, axis=1, keepdims=True))
        probabilities_matrix = exp_dec / np.sum(exp_dec, axis=1, keepdims=True)

    results = []
    for i, probs in enumerate(probabilities_matrix):
        best_idx = int(np.argmax(probs))
        confidence = float(probs[best_idx])
        prob_dict = {
            classes[c_idx]: round(float(probs[c_idx]), 4)
            for c_idx in range(len(classes))
        }
        results.append({
            "text": texts[i],
            "predicted_label": classes[best_idx],
            "confidence": round(confidence, 4),
            "probabilities": prob_dict
        })
    return results
