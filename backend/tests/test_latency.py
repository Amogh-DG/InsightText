import time

def test_single_text_inference_latency(client, analyst_headers):
    payload = {"text": "Package arrived two days late and the box was slightly damaged."}
    
    warmup_res = client.post("/api/v1/predict", json=payload, headers=analyst_headers)
    assert warmup_res.status_code == 200

    durations = []
    for _ in range(5):
        start = time.perf_counter()
        res = client.post("/api/v1/predict", json=payload, headers=analyst_headers)
        elapsed = time.perf_counter() - start
        assert res.status_code == 200
        durations.append(elapsed)

    min_latency = min(durations)
    avg_latency = sum(durations) / len(durations)

    assert min_latency < 0.5, f"Latency {min_latency * 1000:.2f}ms exceeds 500ms threshold"
    assert avg_latency < 0.5, f"Average latency {avg_latency * 1000:.2f}ms exceeds 500ms threshold"
