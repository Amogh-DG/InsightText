from collections import Counter
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.core.rbac import require_roles
from app.models.all_models import (
    User,
    Dataset,
    Document,
    Topic,
    Analysis,
    ModelVersion,
    Prediction,
    Feedback
)
from app.services.crypto import crypto_service

router = APIRouter(prefix="/graph", tags=["graph"])

@router.get("/semantic")
def get_semantic_graph(
    dataset_id: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin"))
):
    if dataset_id:
        ds = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    else:
        ds = db.query(Dataset).order_by(Dataset.created_at.desc()).first()

    if not ds:
        return {"nodes": [], "edges": []}

    target_dataset_id = ds.id
    documents = db.query(Document).filter(Document.dataset_id == target_dataset_id).all()
    if not documents:
        return {"nodes": [], "edges": []}

    doc_ids = [d.id for d in documents]
    analyses = db.query(Analysis).filter(Analysis.document_id.in_(doc_ids)).all()
    analysis_by_doc = {a.document_id: a for a in analyses}

    topics = db.query(Topic).filter(Topic.dataset_id == target_dataset_id).all()
    topic_by_id = {t.id: t for t in topics}

    entity_counts = Counter()
    entity_display_map: Dict[str, str] = {}
    for a in analyses:
        if a.entities:
            for ent in a.entities:
                raw_txt = str(ent.get("text", "")).strip()
                if len(raw_txt) >= 2:
                    k = raw_txt.lower()
                    entity_counts[k] += 1
                    if k not in entity_display_map:
                        entity_display_map[k] = raw_txt

    top_40_entity_keys = set(k for k, _ in entity_counts.most_common(40))

    node_docs: Dict[str, int] = Counter()
    node_sentiment: Dict[str, Dict[str, int]] = {}
    edge_weights: Dict[tuple, int] = Counter()

    for doc in documents:
        doc_node_ids = set()
        a = analysis_by_doc.get(doc.id)
        if a and a.topic_id and a.topic_id in topic_by_id:
            doc_node_ids.add(f"topic_{a.topic_id}")

        if doc.label and doc.label.strip():
            doc_node_ids.add(f"category_{doc.label.strip()}")

        if a and a.entities:
            for ent in a.entities:
                raw_txt = str(ent.get("text", "")).strip()
                k = raw_txt.lower()
                if k in top_40_entity_keys:
                    doc_node_ids.add(f"entity_{k}")

        sent_raw = a.sentiment_label.lower() if (a and a.sentiment_label) else "neutral"
        if "pos" in sent_raw:
            sent_key = "positive"
        elif "neg" in sent_raw:
            sent_key = "negative"
        else:
            sent_key = "neutral"

        for nid in doc_node_ids:
            node_docs[nid] += 1
            if nid not in node_sentiment:
                node_sentiment[nid] = {"negative": 0, "neutral": 0, "positive": 0}
            node_sentiment[nid][sent_key] += 1

        sorted_doc_nodes = sorted(list(doc_node_ids))
        for i in range(len(sorted_doc_nodes)):
            for j in range(i + 1, len(sorted_doc_nodes)):
                u, v = sorted_doc_nodes[i], sorted_doc_nodes[j]
                edge_weights[(u, v)] += 1

    if not node_docs:
        return {"nodes": [], "edges": []}

    kept_nodes = sorted(node_docs.keys(), key=lambda x: node_docs[x], reverse=True)[:120]
    kept_node_set = set(kept_nodes)

    min_weight = 2 if len(documents) > 20 else 1
    edge_candidates = [
        ((u, v), w)
        for (u, v), w in edge_weights.items()
        if w >= min_weight and u in kept_node_set and v in kept_node_set
    ]
    if not edge_candidates and edge_weights:
        edge_candidates = [
            ((u, v), w)
            for (u, v), w in edge_weights.items()
            if u in kept_node_set and v in kept_node_set
        ]

    edge_candidates.sort(key=lambda x: x[1], reverse=True)
    selected_edges = edge_candidates[:250]

    node_connections: Dict[str, int] = Counter()
    edges_output = []
    for (u, v), w in selected_edges:
        edges_output.append({
            "id": f"{u}-{v}",
            "source": u,
            "target": v,
            "weight": w
        })
        node_connections[u] += 1
        node_connections[v] += 1

    nodes_output = []
    for nid in kept_nodes:
        if nid.startswith("topic_"):
            tid = nid[6:]
            t = topic_by_id.get(tid)
            if t and t.keywords:
                label = ", ".join(t.keywords[:2]).title()
            else:
                label = f"Topic {tid[:4]}"
            ntype = "topic"
        elif nid.startswith("category_"):
            label = nid[9:]
            ntype = "category"
        elif nid.startswith("entity_"):
            ekey = nid[7:]
            label = entity_display_map.get(ekey, ekey.title())
            ntype = "entity"
        else:
            label = nid
            ntype = "entity"

        sent_counts = node_sentiment.get(nid, {"negative": 0, "neutral": 0, "positive": 0})
        total_s = sent_counts["negative"] + sent_counts["neutral"] + sent_counts["positive"]
        if total_s > 0:
            sentiment_pct = {
                "negative": round((sent_counts["negative"] / total_s) * 100, 1),
                "neutral": round((sent_counts["neutral"] / total_s) * 100, 1),
                "positive": round((sent_counts["positive"] / total_s) * 100, 1),
            }
        else:
            sentiment_pct = {"negative": 0.0, "neutral": 0.0, "positive": 0.0}

        nodes_output.append({
            "id": nid,
            "label": label,
            "type": ntype,
            "document_count": node_docs[nid],
            "connection_count": node_connections[nid],
            "sentiment": sentiment_pct
        })

    return {
        "nodes": nodes_output,
        "edges": edges_output
    }

@router.get("/semantic/node/{id}/documents")
def get_node_documents(
    id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50),
    dataset_id: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin"))
):
    query = db.query(Document).join(Analysis, Document.id == Analysis.document_id)
    if dataset_id:
        query = query.filter(Document.dataset_id == dataset_id)

    matching_docs = []
    if id.startswith("topic_"):
        tid = id[6:]
        query = query.filter(Analysis.topic_id == tid)
        total = query.count()
        docs = query.order_by(Document.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
        for doc in docs:
            txt = crypto_service.decrypt(doc.text_encrypted)
            matching_docs.append({
                "id": doc.id,
                "snippet": txt[:140] + ("..." if len(txt) > 140 else ""),
                "label": doc.label,
                "sentiment": doc.analysis.sentiment_label if doc.analysis else None,
                "confidence": round(doc.analysis.sentiment_score * 100, 1) if doc.analysis else None,
                "timestamp": doc.timestamp.strftime("%Y-%m-%d") if doc.timestamp else None
            })
    elif id.startswith("category_"):
        cat_name = id[9:]
        query = query.filter(Document.label == cat_name)
        total = query.count()
        docs = query.order_by(Document.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
        for doc in docs:
            txt = crypto_service.decrypt(doc.text_encrypted)
            matching_docs.append({
                "id": doc.id,
                "snippet": txt[:140] + ("..." if len(txt) > 140 else ""),
                "label": doc.label,
                "sentiment": doc.analysis.sentiment_label if doc.analysis else None,
                "confidence": round(doc.analysis.sentiment_score * 100, 1) if doc.analysis else None,
                "timestamp": doc.timestamp.strftime("%Y-%m-%d") if doc.timestamp else None
            })
    elif id.startswith("entity_"):
        ent_key = id[7:].lower()
        all_candidate_docs = query.order_by(Document.created_at.desc()).all()
        filtered = []
        for doc in all_candidate_docs:
            if doc.analysis and doc.analysis.entities:
                if any(str(e.get("text", "")).strip().lower() == ent_key for e in doc.analysis.entities):
                    filtered.append(doc)
        total = len(filtered)
        start_idx = (page - 1) * page_size
        paged_docs = filtered[start_idx : start_idx + page_size]
        for doc in paged_docs:
            txt = crypto_service.decrypt(doc.text_encrypted)
            matching_docs.append({
                "id": doc.id,
                "snippet": txt[:140] + ("..." if len(txt) > 140 else ""),
                "label": doc.label,
                "sentiment": doc.analysis.sentiment_label if doc.analysis else None,
                "confidence": round(doc.analysis.sentiment_score * 100, 1) if doc.analysis else None,
                "timestamp": doc.timestamp.strftime("%Y-%m-%d") if doc.timestamp else None
            })
    else:
        total = 0

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "documents": matching_docs
    }

@router.get("/lineage")
def get_system_lineage(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin"))
):
    users = db.query(User).all()
    datasets = db.query(Dataset).order_by(Dataset.created_at.desc()).all()
    models = db.query(ModelVersion).order_by(ModelVersion.created_at.desc()).all()
    predictions = db.query(Prediction).order_by(Prediction.created_at.desc()).all()
    feedbacks = db.query(Feedback).order_by(Feedback.created_at.desc()).all()

    if not users and not datasets and not models:
        return {"nodes": [], "edges": []}

    user_map = {u.id: u for u in users}
    dataset_map = {d.id: d for d in datasets}

    nodes = []
    edges = []

    for u in users:
        nodes.append({
            "id": f"user_{u.id}",
            "label": u.name or u.email,
            "type": "user",
            "email": u.email,
            "role": u.role,
            "created_at": u.created_at.isoformat() if u.created_at else None
        })

    for d in datasets:
        nodes.append({
            "id": f"dataset_{d.id}",
            "label": d.name,
            "type": "dataset",
            "row_count": d.row_count,
            "source": d.source,
            "created_at": d.created_at.isoformat() if d.created_at else None
        })
        if d.owner_id and d.owner_id in user_map:
            edges.append({
                "id": f"user_{d.owner_id}-dataset_{d.id}",
                "source": f"user_{d.owner_id}",
                "target": f"dataset_{d.id}",
                "type": "created",
                "label": "created →"
            })

    for m in models:
        metrics = m.metrics or {}
        creator_name = user_map[m.created_by].name if (m.created_by and m.created_by in user_map) else "Admin"
        ds_name = dataset_map[m.dataset_id].name if (m.dataset_id and m.dataset_id in dataset_map) else "Customer feedback"
        is_deployed = (m.status == "deployed")

        f1_val = metrics.get("f1")
        acc_val = metrics.get("accuracy")
        prec_val = metrics.get("precision")
        rec_val = metrics.get("recall")

        nodes.append({
            "id": f"model_{m.id}",
            "model_id": m.id,
            "label": m.version,
            "name": m.name,
            "type": "model",
            "algorithm": m.algorithm,
            "feature_type": m.feature_type,
            "status": m.status,
            "deployed": is_deployed,
            "f1": round(float(f1_val), 4) if f1_val is not None else None,
            "accuracy": round(float(acc_val), 4) if acc_val is not None else None,
            "precision": round(float(prec_val), 4) if prec_val is not None else None,
            "recall": round(float(rec_val), 4) if rec_val is not None else None,
            "created_by": creator_name,
            "trained_on": ds_name,
            "created_at": m.created_at.isoformat() if m.created_at else None
        })

        if m.created_by and m.created_by in user_map:
            edges.append({
                "id": f"user_{m.created_by}-model_{m.id}",
                "source": f"user_{m.created_by}",
                "target": f"model_{m.id}",
                "type": "trained",
                "label": "trained →"
            })

        if m.dataset_id and m.dataset_id in dataset_map:
            edges.append({
                "id": f"dataset_{m.dataset_id}-model_{m.id}",
                "source": f"dataset_{m.dataset_id}",
                "target": f"model_{m.id}",
                "type": "trained_on",
                "label": "trained on →"
            })

    pred_nodes_created = []
    for m in models:
        batch_preds = [p for p in predictions if p.model_version_id == m.id and p.document_id is not None]
        if batch_preds:
            p_node_id = f"pred_batch_{m.id}"
            nodes.append({
                "id": p_node_id,
                "label": f"Batch · {m.version}\n{len(batch_preds):,} predictions",
                "name": f"Batch · {m.name}",
                "type": "prediction",
                "count": len(batch_preds)
            })
            pred_nodes_created.append(p_node_id)
            edges.append({
                "id": f"model_{m.id}-{p_node_id}",
                "source": f"model_{m.id}",
                "target": p_node_id,
                "type": "predicted_with",
                "label": "predicted with →"
            })

        single_preds = [p for p in predictions if p.model_version_id == m.id and p.document_id is None]
        if single_preds:
            p_node_id = f"pred_single_{m.id}"
            nodes.append({
                "id": p_node_id,
                "label": f"Single-text API\n{len(single_preds):,} predictions",
                "name": "Single-text API",
                "type": "prediction",
                "count": len(single_preds)
            })
            pred_nodes_created.append(p_node_id)
            edges.append({
                "id": f"model_{m.id}-{p_node_id}",
                "source": f"model_{m.id}",
                "target": p_node_id,
                "type": "predicted_with",
                "label": "predicted with →"
            })

    if not pred_nodes_created and predictions:
        p_node_id = "pred_general"
        nodes.append({
            "id": p_node_id,
            "label": f"Inference API\n{len(predictions):,} predictions",
            "name": "Inference API",
            "type": "prediction",
            "count": len(predictions)
        })
        pred_nodes_created.append(p_node_id)
        if models:
            edges.append({
                "id": f"model_{models[0].id}-{p_node_id}",
                "source": f"model_{models[0].id}",
                "target": p_node_id,
                "type": "predicted_with",
                "label": "predicted with →"
            })

    if feedbacks:
        fb_node_id = "feedback_group"
        nodes.append({
            "id": fb_node_id,
            "label": f"Corrections\n{len(feedbacks)} this week",
            "name": "Corrections",
            "type": "feedback",
            "count": len(feedbacks)
        })
        for p_id in pred_nodes_created:
            edges.append({
                "id": f"{p_id}-{fb_node_id}",
                "source": p_id,
                "target": fb_node_id,
                "type": "corrected_by",
                "label": "corrected by →"
            })
        reviewer_ids = {f.reviewer_id for f in feedbacks if f.reviewer_id and f.reviewer_id in user_map}
        if not reviewer_ids:
            reviewer_ids = {u.id for u in users if u.role == "reviewer"}
        for rid in sorted(reviewer_ids):
            edges.append({
                "id": f"user_{rid}-{fb_node_id}",
                "source": f"user_{rid}",
                "target": fb_node_id,
                "type": "corrected",
                "label": "corrected →"
            })

    node_ids = {n["id"] for n in nodes}
    valid_edges = [
        e for e in edges
        if e["source"] in node_ids and e["target"] in node_ids
    ]

    return {
        "nodes": nodes,
        "edges": valid_edges
    }
