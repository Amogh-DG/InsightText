from app.models.all_models import Dataset, ModelVersion
from app.services.trainer import train_model_sync
from app.services.evaluator import evaluate_predictions

def test_evaluate_predictions_service():
    y_true = ["Billing", "Delivery", "Billing", "Support"]
    y_pred = ["Billing", "Delivery", "Support", "Support"]
    labels = ["Billing", "Delivery", "Support"]
    metrics = evaluate_predictions(y_true, y_pred, labels)
    assert "accuracy" in metrics
    assert "precision" in metrics
    assert "recall" in metrics
    assert "f1" in metrics
    assert "per_class_report" in metrics
    assert "confusion_matrix" in metrics
    assert metrics["confusion_matrix"]["labels"] == labels

def test_list_models_endpoint(client, scientist_headers):
    res = client.get("/api/v1/models", headers=scientist_headers)
    assert res.status_code == 200
    assert isinstance(res.json(), list)
    assert len(res.json()) > 0

def test_get_and_evaluate_model(client, scientist_headers, db_session):
    mv = db_session.query(ModelVersion).filter(ModelVersion.status == "deployed").first()
    assert mv is not None

    res = client.get(f"/api/v1/models/{mv.id}", headers=scientist_headers)
    assert res.status_code == 200
    assert res.json()["id"] == mv.id

    eval_res = client.post(f"/api/v1/models/{mv.id}/evaluate", headers=scientist_headers)
    assert eval_res.status_code == 200
    data = eval_res.json()
    assert "accuracy" in data
    assert "f1" in data
    assert "confusion_matrix" in data

def test_train_model_endpoint(client, scientist_headers, db_session):
    ds = db_session.query(Dataset).first()
    assert ds is not None

    res = client.post("/api/v1/models/train", json={
        "dataset_id": ds.id,
        "algorithm": "Random Forest",
        "feature_type": "TF-IDF",
        "test_split": 0.2
    }, headers=scientist_headers)
    assert res.status_code == 202
    assert res.json()["status"] == "training"
