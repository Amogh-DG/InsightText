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
