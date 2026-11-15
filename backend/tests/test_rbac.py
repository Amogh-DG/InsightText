def test_analyst_cannot_train(client, analyst_headers):
    res = client.post("/api/v1/models/train", json={
        "dataset_id": "dummy",
        "algorithm": "XGBoost",
        "feature_type": "TF-IDF"
    }, headers=analyst_headers)
    assert res.status_code == 403
    assert res.json()["error"]["code"] == "FORBIDDEN"

def test_manager_cannot_upload(client, manager_headers):
    res = client.post(
        "/api/v1/datasets/upload",
        files={"file": ("test.csv", b"col1,col2\na,b", "text/csv")},
        data={"name": "test", "text_column": "col1"},
        headers=manager_headers
    )
    assert res.status_code == 403
    assert res.json()["error"]["code"] == "FORBIDDEN"

def test_non_admin_cannot_list_users(client, analyst_headers):
    res = client.get("/api/v1/users", headers=analyst_headers)
    assert res.status_code == 403
    assert res.json()["error"]["code"] == "FORBIDDEN"

def test_admin_can_list_users(client, admin_headers):
    res = client.get("/api/v1/users", headers=admin_headers)
    assert res.status_code == 200
    assert isinstance(res.json(), list)
