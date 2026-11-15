from app.services.semantic import (
    analyze_sentiment,
    extract_entities,
    classify_intent,
    extract_topics,
    analyze_single_text
)
from app.models.all_models import Dataset

def test_analyze_sentiment():
    pos = analyze_sentiment("I absolutely love this product, it is magnificent!")
    assert pos["label"] == "Positive"
    assert pos["score"] >= 0.5

    neg = analyze_sentiment("This is completely broken, terrible and useless.")
    assert neg["label"] == "Negative"
    assert neg["score"] >= 0.5

def test_extract_entities():
    ents = extract_entities("Google and Microsoft signed a contract in New York on Monday.")
    texts = [e["text"] for e in ents]
    assert any("Google" in t or "Microsoft" in t or "New York" in t for t in texts)

def test_classify_intent():
    res = classify_intent("I want to know how much the annual plan costs.")
    assert res["intent"] in ["inquiry", "request", "complaint", "other"]
    assert res["score"] >= 0.0

def test_extract_topics():
    texts = [
        "Refund not received on credit card payment",
        "Charge was duplicated on invoice statement",
        "Delivery courier arrived late with damaged box",
        "Package delayed in transit hub",
        "App crashes upon login screen on iPhone",
        "Software freezes when clicking export button"
    ]
    topics = extract_topics(texts, num_topics=2)
    assert len(topics) == 2
    for t in topics:
        assert len(t["keywords"]) > 0
        assert t["size"] > 0

def test_semantic_analysis_endpoint(client, analyst_headers):
    res = client.post("/api/v1/analysis/text", json={
        "text": "Charged twice by Northwind for my March plan."
    }, headers=analyst_headers)
    assert res.status_code == 200
    data = res.json()
    assert "sentiment_label" in data
    assert "entities" in data
    assert "intent" in data
    assert "low_confidence" in data

def test_similar_documents_assigned_same_topic():
    from app.services.semantic import extract_topics_with_assignments
    texts = [
        "Refund not received on credit card payment billing invoice",
        "Charge was duplicated on invoice statement credit card refund",
        "Software freezes when clicking export button app crash bug",
        "App crashes upon login screen and application freezes bug"
    ]
    topics, assignments = extract_topics_with_assignments(texts, num_topics=2)
    assert len(topics) == 2
    assert assignments[0] == assignments[1]
    assert assignments[2] == assignments[3]
    assert assignments[0] != assignments[2]

def test_get_dataset_analysis_summary(client, analyst_headers, db_session):
    ds = db_session.query(Dataset).first()
    if ds:
        res = client.get(f"/api/v1/analysis/{ds.id}/summary", headers=analyst_headers)
        assert res.status_code == 200
        data = res.json()
        assert "sentiment_summary" in data
        assert "top_intents" in data
        assert "dominant_sentiment" in data
        assert "most_frequent_intent" in data
        assert "total_analyzed" in data
