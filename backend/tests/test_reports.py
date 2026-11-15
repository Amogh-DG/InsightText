from app.models.all_models import Dataset

def test_reports_summary_endpoint(client, analyst_headers):
    res = client.get("/api/v1/reports/summary", headers=analyst_headers)
    assert res.status_code == 200
    data = res.json()
    assert "documents_processed" in data
    assert "documents_delta_pct" in data
    assert "datasets_count" in data
    assert "datasets_added_this_month" in data
    assert "predictions_today" in data
    assert "predictions_today_delta_pct" in data
    assert "sentiment_distribution" in data
    assert "label_distribution" in data
    assert "key_findings" in data
    assert isinstance(data["key_findings"], list)

def test_reports_summary_with_filters(client, analyst_headers, db_session):
    ds = db_session.query(Dataset).first()
    assert ds is not None
    res = client.get(
        f"/api/v1/reports/summary?dataset_id={ds.id}&start_date=2026-01-01&end_date=2026-12-31",
        headers=analyst_headers
    )
    assert res.status_code == 200
    data = res.json()
    assert data["documents_processed"] >= 0

def test_reports_export_csv_and_html(client, analyst_headers):
    res_csv = client.get("/api/v1/reports/export?format=csv", headers=analyst_headers)
    assert res_csv.status_code == 200
    assert "text/csv" in res_csv.headers["content-type"]
    assert "document_id" in res_csv.text

    res_html = client.get("/api/v1/reports/export?format=html", headers=analyst_headers)
    assert res_html.status_code == 200
    assert "text/html" in res_html.headers["content-type"]
    assert "InsightText" in res_html.text
    assert "Key Findings" in res_html.text
