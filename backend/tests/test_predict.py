def test_single_predict_jwt(client, analyst_headers):
    res = client.post("/api/v1/predict", json={
        "text": "Package arrived late and the box was crushed."
    }, headers=analyst_headers)
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert "predicted_label" in data[0]
    assert "confidence" in data[0]
    assert "probabilities" in data[0]

def test_single_predict_api_key(client, api_key_headers):
    res = client.post("/api/v1/predict", json={
        "text": "Charged twice on my credit card."
    }, headers=api_key_headers)
    assert res.status_code == 200
    assert len(res.json()) == 1

def test_batch_predict(client, analyst_headers):
    texts = [
        "Refund still not received.",
        "App crashed during checkout.",
        "Representative was very helpful."
    ]
    res = client.post("/api/v1/predict/batch", json={
        "texts": texts
    }, headers=analyst_headers)
    assert res.status_code == 200
    results = res.json()
    assert len(results) == 3
    for r in results:
        assert r["confidence"] > 0

def test_predict_trend(client, analyst_headers):
    res = client.post("/api/v1/predict/trend", json={
        "target": "negative_sentiment",
        "periods": 7
    }, headers=analyst_headers)
    assert res.status_code == 200
    data = res.json()
    assert "points" in data
    assert "summary_text" in data
    assert len(data["points"]) > 0

def test_classify_text(client, analyst_headers):
    res = client.post("/api/v1/classify", json={
        "text": "I was billed twice this month and support has not answered."
    }, headers=analyst_headers)
    assert res.status_code == 200
    assert len(res.json()) == 1
