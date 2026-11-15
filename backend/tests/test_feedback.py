from app.models.all_models import Prediction

def test_list_predictions(client, reviewer_headers):
    res = client.get("/api/v1/predictions", headers=reviewer_headers)
    assert res.status_code == 200
    assert isinstance(res.json(), list)

def test_submit_feedback(client, reviewer_headers, db_session):
    pred = db_session.query(Prediction).first()
    assert pred is not None

    res = client.post("/api/v1/feedback", json={
        "prediction_id": pred.id,
        "corrected_label": "Billing",
        "comment": "Clearly a billing discrepancy",
        "status": "submitted"
    }, headers=reviewer_headers)
    assert res.status_code == 201
    data = res.json()
    assert data["prediction_id"] == pred.id
    assert data["corrected_label"] == "Billing"

def test_list_feedbacks(client, reviewer_headers):
    res = client.get("/api/v1/feedback", headers=reviewer_headers)
    assert res.status_code == 200
    assert isinstance(res.json(), list)
    assert len(res.json()) > 0

def test_submit_feedback_unlinked_prediction(client, reviewer_headers, db_session):
    from app.services.crypto import crypto_service
    from app.models.all_models import Dataset, Document
    unlinked_pred = Prediction(
        input_text_encrypted=crypto_service.encrypt("Ad-hoc unlinked prediction for feedback test"),
        predicted_label="Support",
        confidence=0.55,
        probabilities={"Support": 0.55, "Billing": 0.45}
    )
    db_session.add(unlinked_pred)
    db_session.commit()
    db_session.refresh(unlinked_pred)

    res = client.post("/api/v1/feedback", json={
        "prediction_id": unlinked_pred.id,
        "corrected_label": "Billing",
        "comment": "Unlinked prediction correction",
        "status": "submitted"
    }, headers=reviewer_headers)
    assert res.status_code == 201

    accum_ds = db_session.query(Dataset).filter(Dataset.name == "Accumulated Feedback").first()
    assert accum_ds is not None
    assert accum_ds.row_count >= 1
    db_session.refresh(unlinked_pred)
    doc = db_session.query(Document).filter(Document.id == unlinked_pred.document_id).first()
    assert doc is not None
    assert doc.label == "Billing"
    assert crypto_service.decrypt(doc.text_encrypted) == "Ad-hoc unlinked prediction for feedback test"

def test_retrain_endpoint(client, scientist_headers):
    res = client.post("/api/v1/feedback/retrain", headers=scientist_headers)
    assert res.status_code in [200, 202]
    data = res.json()
    assert "model_id" in data
    assert "status" in data
