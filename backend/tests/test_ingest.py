def test_ingest_via_api_key(client, api_key_headers):
    payload = {
        "name": "External API Ingest",
        "text_column": "feedback",
        "label_column": "category",
        "records": [
            {"feedback": "App stopped syncing data", "category": "Product quality"},
            {"feedback": "Fast delivery appreciated", "category": "Delivery"}
        ]
    }
    res = client.post("/api/v1/ingest", json=payload, headers=api_key_headers)
    assert res.status_code == 201
    data = res.json()
    assert data["name"] == "External API Ingest"
    assert data["row_count"] == 2
    assert data["source"] == "api"

def test_ingest_via_jwt(client, analyst_headers):
    payload = {
        "name": "Analyst API Ingest",
        "text_column": "text",
        "records": [
            {"text": "Simple test payload", "meta": "test"}
        ]
    }
    res = client.post("/api/v1/ingest", json=payload, headers=analyst_headers)
    assert res.status_code == 201
    assert res.json()["row_count"] == 1

def test_ingest_unauthorized(client):
    payload = {"records": [{"text": "Unauthorized"}]}
    res = client.post("/api/v1/ingest", json=payload)
    assert res.status_code == 401
    assert res.json()["error"]["code"] == "UNAUTHORIZED"

def test_file_upload_csv(client, analyst_headers):
    csv_content = b"text,label,date\nGreat support,Support,2026-03-01\nLate package,Delivery,2026-03-02\n"
    res = client.post(
        "/api/v1/datasets/upload",
        files={"file": ("tickets.csv", csv_content, "text/csv")},
        data={"name": "Tickets CSV", "text_column": "text", "label_column": "label", "time_column": "date"},
        headers=analyst_headers
    )
    assert res.status_code == 201
    data = res.json()
    assert data["name"] == "Tickets CSV"
    assert data["row_count"] == 2

def test_file_preview(client, analyst_headers):
    csv_content = b"content,sentiment\nI loved the update,Positive\n"
    res = client.post(
        "/api/v1/datasets/preview",
        files={"file": ("preview.csv", csv_content, "text/csv")},
        headers=analyst_headers
    )
    assert res.status_code == 200
    data = res.json()
    assert "columns" in data
    assert "content" in data["columns"]
    assert len(data["rows"]) == 1

def test_invalid_column_mapping(client, analyst_headers):
    csv_content = b"text,label\nGood,Positive\n"
    res = client.post(
        "/api/v1/datasets/upload",
        files={"file": ("data.csv", csv_content, "text/csv")},
        data={"name": "Bad Mapping", "text_column": "non_existent"},
        headers=analyst_headers
    )
    assert res.status_code == 400
    assert res.json()["error"]["code"] == "INVALID_COLUMN_MAPPING"

def test_file_upload_xlsx(client, analyst_headers):
    import io
    import openpyxl
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(["text", "label", "date"])
    ws.append(["Xlsx test support message", "Support", "2026-03-01"])
    ws.append(["Xlsx delivery delay issue", "Delivery", "2026-03-02"])
    out = io.BytesIO()
    wb.save(out)
    xlsx_bytes = out.getvalue()

    res = client.post(
        "/api/v1/datasets/upload",
        files={"file": ("tickets.xlsx", xlsx_bytes, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
        data={"name": "Tickets XLSX", "text_column": "text", "label_column": "label", "time_column": "date"},
        headers=analyst_headers
    )
    assert res.status_code == 201
    data = res.json()
    assert data["name"] == "Tickets XLSX"
    assert data["row_count"] == 2

def test_upload_validation_error_and_error_report(client, analyst_headers):
    csv_content = b"text,label,date\n,Support,invalid-date\n"
    res = client.post(
        "/api/v1/datasets/upload",
        files={"file": ("invalid.csv", csv_content, "text/csv")},
        data={"name": "Invalid File", "text_column": "text", "label_column": "label", "time_column": "date"},
        headers=analyst_headers
    )
    assert res.status_code == 400
    err = res.json()["error"]
    assert err["code"] == "IMPORT_FAILED"
    assert "details" in err
    assert len(err["details"]) > 0

    err_report_res = client.post(
        "/api/v1/datasets/error-report",
        json=err["details"],
        headers=analyst_headers
    )
    assert err_report_res.status_code == 200
    assert "text/csv" in err_report_res.headers["content-type"]
    assert "Row 1" in err_report_res.text
