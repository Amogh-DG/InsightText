from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, BackgroundTasks, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.db import get_db, SessionLocal
from app.core.deps import get_current_user, record_audit_log
from app.core.rbac import require_roles
from app.core.errors import AppException
from app.models.all_models import User, Dataset, Document, Analysis, Topic, SystemSetting
from app.schemas.all_schemas import (
    AnalysisRunRequest,
    SemanticTextRequest,
    SemanticTextResponse,
    TopicResponse
)
from app.services.semantic import (
    analyze_single_text,
    extract_topics_with_assignments,
    analyze_sentiment,
    extract_entities,
    classify_intent
)
from app.services.crypto import crypto_service
from app.config import settings

router = APIRouter(prefix="/analysis", tags=["analysis"])

def run_dataset_analysis_task(dataset_id: str, analysis_types: List[str], num_topics: int = 6):
    db = SessionLocal()
    try:
        setting_th = db.query(SystemSetting).filter(SystemSetting.key == "confidence_threshold").first()
        threshold = float(setting_th.value) if setting_th else settings.CONFIDENCE_THRESHOLD
        
        setting_intent = db.query(SystemSetting).filter(SystemSetting.key == "intent_labels").first()
        intent_labels = setting_intent.value if setting_intent else settings.INTENT_LABELS

        docs = db.query(Document).filter(Document.dataset_id == dataset_id).all()
        decrypted_texts = []
        for doc in docs:
            decrypted_texts.append(crypto_service.decrypt(doc.text_encrypted))

        topic_mapping = {}
        cluster_assignments = []
        if "topics" in analysis_types and decrypted_texts:
            db.query(Topic).filter(Topic.dataset_id == dataset_id).delete()
            db.commit()

            raw_topics, cluster_assignments = extract_topics_with_assignments(decrypted_texts, num_topics=num_topics)
            for rt in raw_topics:
                top_obj = Topic(
                    dataset_id=dataset_id,
                    keywords=rt["keywords"],
                    size=rt["size"]
                )
                db.add(top_obj)
                db.flush()
                topic_mapping[rt["topic_id"]] = top_obj.id
            db.commit()

        for i, doc in enumerate(docs):
            txt = decrypted_texts[i]
            existing_analysis = db.query(Analysis).filter(Analysis.document_id == doc.id).first()
            if existing_analysis:
                db.delete(existing_analysis)

            sentiment = analyze_sentiment(txt) if "sentiment" in analysis_types else {"label": "Neutral", "score": 0.5}
            entities = extract_entities(txt) if "entities" in analysis_types else []
            intent_res = classify_intent(txt, intent_labels) if "intent" in analysis_types else {"intent": "other", "score": 0.5}

            low_conf = (sentiment["score"] < threshold) or (intent_res["score"] < threshold)

            assigned_topic_id = None
            if topic_mapping and i < len(cluster_assignments):
                assigned_topic_id = topic_mapping.get(cluster_assignments[i])

            analysis_obj = Analysis(
                document_id=doc.id,
                sentiment_label=sentiment["label"],
                sentiment_score=sentiment["score"],
                entities=entities,
                intent=intent_res["intent"],
                intent_score=intent_res["score"],
                topic_id=assigned_topic_id,
                low_confidence=low_conf
            )
            db.add(analysis_obj)
            doc.processed = True

        db.commit()
    finally:
        db.close()

@router.post("/run", status_code=status.HTTP_202_ACCEPTED)
def run_analysis(
    payload: AnalysisRunRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("analyst", "data_scientist"))
):
    dataset = db.query(Dataset).filter(Dataset.id == payload.dataset_id).first()
    if not dataset:
        raise AppException(status.HTTP_404_NOT_FOUND, "DATASET_NOT_FOUND", "Dataset not found")

    docs_count = db.query(func.count(Document.id)).filter(Document.dataset_id == payload.dataset_id).scalar()
    if docs_count <= 50:
        run_dataset_analysis_task(payload.dataset_id, payload.analysis_types, payload.num_topics or 6)
    else:
        background_tasks.add_task(
            run_dataset_analysis_task,
            payload.dataset_id,
            payload.analysis_types,
            payload.num_topics or 6
        )

    record_audit_log(db, current_user.id, "RUN_ANALYSIS", {"dataset_id": payload.dataset_id, "types": payload.analysis_types})
    return {"status": "started", "dataset_id": payload.dataset_id}

@router.post("/text", response_model=SemanticTextResponse)
def analyze_text(
    payload: SemanticTextRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("analyst", "data_scientist"))
):
    setting_th = db.query(SystemSetting).filter(SystemSetting.key == "confidence_threshold").first()
    threshold = float(setting_th.value) if setting_th else settings.CONFIDENCE_THRESHOLD
    
    setting_intent = db.query(SystemSetting).filter(SystemSetting.key == "intent_labels").first()
    intent_labels = setting_intent.value if setting_intent else settings.INTENT_LABELS

    result = analyze_single_text(payload.text, threshold=threshold, intent_labels=intent_labels)
    return result

@router.get("/{dataset_id}/results")
def get_analysis_results(
    dataset_id: str,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise AppException(status.HTTP_404_NOT_FOUND, "DATASET_NOT_FOUND", "Dataset not found")

    analyses = (
        db.query(Analysis)
        .join(Document, Analysis.document_id == Document.id)
        .filter(Document.dataset_id == dataset_id)
        .offset(skip)
        .limit(limit)
        .all()
    )

    results = []
    for a in analyses:
        txt = crypto_service.decrypt(a.document.text_encrypted) if a.document else ""
        results.append({
            "id": a.id,
            "document_id": a.document_id,
            "text": txt,
            "sentiment_label": a.sentiment_label,
            "sentiment_score": a.sentiment_score,
            "entities": a.entities,
            "intent": a.intent,
            "intent_score": a.intent_score,
            "topic_id": a.topic_id,
            "low_confidence": a.low_confidence,
            "created_at": a.created_at
        })
    return results

@router.get("/{dataset_id}/summary")
def get_analysis_summary(
    dataset_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise AppException(status.HTTP_404_NOT_FOUND, "DATASET_NOT_FOUND", "Dataset not found")

    analyses = (
        db.query(Analysis)
        .join(Document, Analysis.document_id == Document.id)
        .filter(Document.dataset_id == dataset_id)
        .all()
    )

    if not analyses:
        return {
            "sentiment_summary": {"Positive": 0.0, "Neutral": 0.0, "Negative": 0.0},
            "top_intents": {},
            "dominant_sentiment": "None",
            "most_frequent_intent": "None",
            "total_analyzed": 0
        }

    total = len(analyses)
    sent_counts = {"Positive": 0, "Neutral": 0, "Negative": 0}
    intent_counts = {}

    for a in analyses:
        s_lbl = a.sentiment_label.capitalize()
        if s_lbl in sent_counts:
            sent_counts[s_lbl] += 1
        else:
            sent_counts[s_lbl] = 1

        i_lbl = a.intent.replace("_", " ").capitalize()
        intent_counts[i_lbl] = intent_counts.get(i_lbl, 0) + 1

    sent_summary = {
        k: round((v / total) * 100, 1)
        for k, v in sent_counts.items()
    }
    top_intents = {
        k: round((v / total) * 100, 1)
        for k, v in sorted(intent_counts.items(), key=lambda item: item[1], reverse=True)[:5]
    }

    dominant_sentiment = max(sent_counts.items(), key=lambda item: item[1])[0] if sent_counts else "Neutral"
    most_frequent_intent = max(intent_counts.items(), key=lambda item: item[1])[0] if intent_counts else "Other"

    return {
        "sentiment_summary": sent_summary,
        "top_intents": top_intents,
        "dominant_sentiment": dominant_sentiment,
        "most_frequent_intent": most_frequent_intent,
        "total_analyzed": total
    }

@router.get("/{dataset_id}/topics", response_model=List[TopicResponse])
def get_dataset_topics(
    dataset_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return db.query(Topic).filter(Topic.dataset_id == dataset_id).all()
