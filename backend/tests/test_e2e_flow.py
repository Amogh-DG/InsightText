import io
import time
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_full_acceptance_criteria_flow():
    login_res = client.post("/api/v1/auth/login", json={
        "email": "priya.nair@northwind.io",
        "password": "Password123!"
    })
    assert login_res.status_code == 200
    admin_token = login_res.json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    analyst_login = client.post("/api/v1/auth/login", json={
        "email": "analyst@example.com",
        "password": "Analyst123!"
    })
    assert analyst_login.status_code == 200
    analyst_token = analyst_login.json()["access_token"]
    analyst_headers = {"Authorization": f"Bearer {analyst_token}"}

    scientist_login = client.post("/api/v1/auth/login", json={
        "email": "scientist@example.com",
        "password": "Scientist123!"
    })
    assert scientist_login.status_code == 200
    scientist_token = scientist_login.json()["access_token"]
    scientist_headers = {"Authorization": f"Bearer {scientist_token}"}

    manager_login = client.post("/api/v1/auth/login", json={
        "email": "manager@example.com",
        "password": "Manager123!"
    })
    assert manager_login.status_code == 200
    manager_token = manager_login.json()["access_token"]
    manager_headers = {"Authorization": f"Bearer {manager_token}"}

    reviewer_login = client.post("/api/v1/auth/login", json={
        "email": "reviewer@example.com",
        "password": "Reviewer123!"
    })
    assert reviewer_login.status_code == 200
    reviewer_token = reviewer_login.json()["access_token"]
    reviewer_headers = {"Authorization": f"Bearer {reviewer_token}"}

    csv_data = (
        "feedback_text,category,created_at\n"
        "Charged twice on my credit card plan,Billing,2026-03-01 10:00:00\n"
        "Package arrived late and severely broken,Delivery,2026-03-02 11:00:00\n"
        "App crashes when viewing reports dashboard,Product quality,2026-03-03 12:00:00\n"
        "Support agent answered my questions kindly,Support,2026-03-04 13:00:00\n"
        "Refund taking over two weeks to process,Billing,2026-03-05 14:00:00\n"
        "Shipment delayed due to courier backlog,Delivery,2026-03-06 15:00:00\n"
        "Software freezes when clicking the button,Product quality,2026-03-07 16:00:00\n"
        "Help desk provided clear instructions,Support,2026-03-08 17:00:00\n"
        "Unexpected fee appeared on invoice,Billing,2026-03-09 18:00:00\n"
        "Delivery driver arrived early,Delivery,2026-03-10 19:00:00\n"
        "Screen resolution is blurry,Product quality,2026-03-11 20:00:00\n"
        "Representative resolved problem fast,Support,2026-03-12 21:00:00\n"
    )

    upload_res = client.post(
        "/api/v1/datasets/upload",
        files={"file": ("e2e_tickets.csv", csv_data.encode("utf-8"), "text/csv")},
        data={
            "name": "E2E Test Tickets",
            "text_column": "feedback_text",
            "label_column": "category",
            "time_column": "created_at"
        },
        headers=analyst_headers
    )
    assert upload_res.status_code == 201
    dataset = upload_res.json()
    dataset_id = dataset["id"]

    manager_upload_res = client.post(
        "/api/v1/datasets/upload",
        files={"file": ("mgr.csv", b"text\nhi", "text/csv")},
        data={"name": "Mgr Dataset", "text_column": "text"},
        headers=manager_headers
    )
    assert manager_upload_res.status_code == 403

    analyst_train_attempt = client.post(
        "/api/v1/models/train",
        json={
            "dataset_id": dataset_id,
            "algorithm": "XGBoost",
            "feature_type": "TF-IDF"
        },
        headers=analyst_headers
    )
    assert analyst_train_attempt.status_code == 403

    analyst_users_attempt = client.get("/api/v1/users", headers=analyst_headers)
    assert analyst_users_attempt.status_code == 403

    admin_users_res = client.get("/api/v1/users", headers=admin_headers)
    assert admin_users_res.status_code == 200
    assert len(admin_users_res.json()) >= 6

    analysis_run_res = client.post(
        "/api/v1/analysis/run",
        json={
            "dataset_id": dataset_id,
            "analysis_types": ["sentiment", "entities", "intent", "topics"],
            "num_topics": 2
        },
        headers=analyst_headers
    )
    assert analysis_run_res.status_code == 202

    analysis_res = client.get(f"/api/v1/analysis/{dataset_id}/results", headers=analyst_headers)
    assert analysis_res.status_code == 200
    results_list = analysis_res.json()
    assert len(results_list) > 0
    first_result = results_list[0]
    assert "sentiment_label" in first_result
    assert "intent" in first_result

    analysis_summary = client.get(f"/api/v1/analysis/{dataset_id}/summary", headers=analyst_headers)
    assert analysis_summary.status_code == 200
    assert "sentiment_summary" in analysis_summary.json()

    from app.services.trainer import train_model_sync
    from app.models.all_models import ModelVersion
    from app.db import SessionLocal

    db = SessionLocal()
    mv = ModelVersion(
        name="E2E Ticket Classifier",
        algorithm="XGBoost",
        feature_type="TF-IDF",
        dataset_id=dataset_id,
        version="v1.0",
        artifact_path="",
        metrics={},
        status="training",
        created_by=scientist_login.json()["user"]["id"]
    )
    db.add(mv)
    db.commit()
    db.refresh(mv)

    texts = [
        "Charged twice on my credit card plan",
        "Package arrived late and severely broken",
        "App crashes when viewing reports dashboard",
        "Support agent answered my questions kindly",
        "Refund taking over two weeks to process",
        "Shipment delayed due to courier backlog",
        "Software freezes when clicking the button",
        "Help desk provided clear instructions",
        "Unexpected fee appeared on invoice",
        "Delivery driver arrived early",
        "Screen resolution is blurry",
        "Representative resolved problem fast"
    ]
    labels = [
        "Billing",
        "Delivery",
        "Product quality",
        "Support",
        "Billing",
        "Delivery",
        "Product quality",
        "Support",
        "Billing",
        "Delivery",
        "Product quality",
        "Support"
    ]

    train_model_sync(
        model_version_id=mv.id,
        texts=texts,
        labels=labels,
        algorithm="XGBoost",
        feature_type="TF-IDF",
        test_split=0.25
    )
    db.close()

    eval_res = client.post(f"/api/v1/models/{mv.id}/evaluate", headers=scientist_headers)
    assert eval_res.status_code == 200
    eval_data = eval_res.json()
    assert "accuracy" in eval_data
    assert "confusion_matrix" in eval_data
    assert "matrix" in eval_data["confusion_matrix"]

    deploy_res = client.post(f"/api/v1/models/{mv.id}/deploy", headers=scientist_headers)
    assert deploy_res.status_code == 200
    assert deploy_res.json()["status"] == "deployed"

    pred_res = client.post(
        "/api/v1/predict",
        json={"text": "Delivery arrived three days late and items missing"},
        headers=analyst_headers
    )
    assert pred_res.status_code == 200
    preds = pred_res.json()
    assert len(preds) == 1
    pred_item = preds[0]
    pred_id = pred_item["id"]

    fb_res = client.post(
        "/api/v1/feedback",
        json={
            "prediction_id": pred_id,
            "corrected_label": "Delivery",
            "comment": "Confirmed delivery issue by reviewer",
            "status": "submitted"
        },
        headers=reviewer_headers
    )
    assert fb_res.status_code == 201
    assert fb_res.json()["corrected_label"] == "Delivery"

    dash_res = client.get("/api/v1/reports/summary", headers=manager_headers)
    assert dash_res.status_code == 200
    dash_data = dash_res.json()
    assert dash_data["documents_processed"] > 0
    assert dash_data["datasets_count"] > 0
    assert "sentiment_distribution" in dash_data
    assert "trend_points" in dash_data

    t0 = time.perf_counter()
    lat_res = client.post(
        "/api/v1/predict",
        json={"text": "Quick test for latency check"},
        headers=analyst_headers
    )
    t_elapsed = time.perf_counter() - t0
    assert lat_res.status_code == 200
    assert t_elapsed < 0.500

    del_res = client.delete(f"/api/v1/datasets/{dataset_id}", headers=analyst_headers)
    assert del_res.status_code == 204
