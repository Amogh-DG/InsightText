import csv
import io
from datetime import datetime, date, timedelta
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.all_models import Document, Dataset, ModelVersion, Prediction, Analysis, Topic
from app.services.trends import compute_trend_forecast
from app.services.crypto import crypto_service

def get_dashboard_summary(
    db: Session,
    dataset_id: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
) -> Dict[str, Any]:
    now = datetime.utcnow()
    last_7d = now - timedelta(days=7)
    prev_7d = now - timedelta(days=14)

    doc_query = db.query(Document)
    analysis_query = db.query(Analysis).join(Document, Analysis.document_id == Document.id)

    if dataset_id:
        doc_query = doc_query.filter(Document.dataset_id == dataset_id)
        analysis_query = analysis_query.filter(Document.dataset_id == dataset_id)
    if start_date:
        doc_query = doc_query.filter(Document.created_at >= start_date)
        analysis_query = analysis_query.filter(Document.created_at >= start_date)
    if end_date:
        doc_query = doc_query.filter(Document.created_at <= end_date)
        analysis_query = analysis_query.filter(Document.created_at <= end_date)

    doc_count = doc_query.count()
    dataset_count = db.query(func.count(Dataset.id)).scalar() or 0

    count_last_7 = db.query(func.count(Document.id)).filter(Document.created_at >= last_7d).scalar() or 0
    count_prev_7 = db.query(func.count(Document.id)).filter(Document.created_at >= prev_7d, Document.created_at < last_7d).scalar() or 0
    if count_prev_7 > 0:
        documents_delta_pct = round(((count_last_7 - count_prev_7) / count_prev_7) * 100, 1)
    elif count_last_7 > 0:
        documents_delta_pct = 100.0
    else:
        documents_delta_pct = 0.0

    month_start = datetime(now.year, now.month, 1)
    datasets_added_this_month = db.query(func.count(Dataset.id)).filter(Dataset.created_at >= month_start).scalar() or 0

    deployed_model = (
        db.query(ModelVersion)
        .filter(ModelVersion.status == "deployed")
        .order_by(ModelVersion.created_at.desc())
        .first()
    )
    if not deployed_model:
        deployed_model = (
            db.query(ModelVersion)
            .filter(ModelVersion.status == "trained")
            .order_by(ModelVersion.created_at.desc())
            .first()
        )
        
    deployed_f1 = None
    deployed_name = None
    if deployed_model:
        deployed_name = f"{deployed_model.name} {deployed_model.version}"
        if deployed_model.metrics and "f1" in deployed_model.metrics:
            deployed_f1 = float(deployed_model.metrics["f1"])

    today_start = datetime.combine(date.today(), datetime.min.time())
    yesterday_start = today_start - timedelta(days=1)
    predictions_today = (
        db.query(func.count(Prediction.id))
        .filter(Prediction.created_at >= today_start)
        .scalar() or 0
    )
    predictions_yesterday = (
        db.query(func.count(Prediction.id))
        .filter(Prediction.created_at >= yesterday_start, Prediction.created_at < today_start)
        .scalar() or 0
    )
    if predictions_yesterday > 0:
        predictions_today_delta_pct = round(((predictions_today - predictions_yesterday) / predictions_yesterday) * 100, 1)
    elif predictions_today > 0:
        predictions_today_delta_pct = 100.0
    else:
        predictions_today_delta_pct = 0.0

    sentiment_counts = (
        analysis_query.with_entities(Analysis.sentiment_label, func.count(Analysis.id))
        .group_by(Analysis.sentiment_label)
        .all()
    )
    total_sentiments = sum(c for _, c in sentiment_counts)
    if total_sentiments > 0:
        sent_dict = {
            label.capitalize(): round((count / total_sentiments) * 100, 1)
            for label, count in sentiment_counts
        }
    else:
        sent_dict = {}

    label_counts = (
        doc_query.filter(Document.label.isnot(None))
        .with_entities(Document.label, func.count(Document.id))
        .group_by(Document.label)
        .order_by(func.count(Document.id).desc())
        .limit(6)
        .all()
    )
    total_labels = sum(c for _, c in label_counts)
    if total_labels > 0:
        label_dict = {
            label: round((count / total_labels) * 100, 1)
            for label, count in label_counts
        }
    else:
        label_dict = {}

    topic_query = db.query(Topic)
    if dataset_id:
        topic_query = topic_query.filter(Topic.dataset_id == dataset_id)
    topics = topic_query.order_by(Topic.size.desc()).limit(5).all()
    total_topic_size = sum(t.size for t in topics)
    topic_sizes = []
    if total_topic_size > 0:
        for t in topics:
            kw = ", ".join(t.keywords[:2]) if t.keywords else f"Topic {t.id[:4]}"
            pct = round((t.size / total_topic_size) * 100, 1)
            topic_sizes.append({"name": kw.capitalize(), "percentage": pct, "count": t.size})

    low_conf_analyses = (
        analysis_query.filter(Analysis.low_confidence == True)
        .order_by(Analysis.created_at.desc())
        .limit(5)
        .all()
    )
    
    recent_low_conf = []
    for a in low_conf_analyses:
        text_plain = crypto_service.decrypt(a.document.text_encrypted) if a.document else ""
        recent_low_conf.append({
            "id": a.id,
            "text": text_plain[:100],
            "predicted": a.intent,
            "confidence": round(a.intent_score * 100, 1)
        })

    trend = compute_trend_forecast(db, dataset_id=dataset_id, periods=7)

    key_findings: List[str] = []
    if "Negative" in sent_dict:
        key_findings.append(f"Negative sentiment accounts for {sent_dict['Negative']}% of analyzed items in this period.")
    elif total_sentiments > 0:
        key_findings.append(f"Analyzed {total_sentiments} documents with zero negative sentiment detected.")
    else:
        key_findings.append("No semantic sentiment analyses recorded for the selected scope.")

    if topic_sizes:
        key_findings.append(f"The primary customer concern cluster is '{topic_sizes[0]['name']}', representing {topic_sizes[0]['percentage']}% of categorized volume ({topic_sizes[0]['count']} documents).")
    else:
        key_findings.append("No topic clusters have been extracted yet.")

    if deployed_model and deployed_f1 is not None:
        met_str = "achieving" if deployed_f1 >= 0.85 else "falling short of"
        key_findings.append(f"Deployed model {deployed_name} reports a macro F1 of {deployed_f1:.2f}, {met_str} the target threshold of 0.85.")
    else:
        key_findings.append("No production model is currently deployed.")

    return {
        "documents_processed": doc_count,
        "documents_delta_pct": documents_delta_pct,
        "datasets_count": dataset_count,
        "datasets_added_this_month": datasets_added_this_month,
        "deployed_model_f1": deployed_f1,
        "deployed_model_name": deployed_name,
        "predictions_today": predictions_today,
        "predictions_today_delta_pct": predictions_today_delta_pct,
        "sentiment_distribution": sent_dict,
        "label_distribution": label_dict,
        "topic_sizes": topic_sizes,
        "recent_low_confidence": recent_low_conf,
        "trend_points": trend["points"],
        "key_findings": key_findings
    }

def generate_csv_report(
    db: Session,
    dataset_id: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
) -> str:
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["document_id", "text", "label", "timestamp", "sentiment", "sentiment_score", "intent", "intent_score", "low_confidence"])
    
    query = db.query(Document)
    if dataset_id:
        query = query.filter(Document.dataset_id == dataset_id)
    if start_date:
        query = query.filter(Document.created_at >= start_date)
    if end_date:
        query = query.filter(Document.created_at <= end_date)
        
    for doc in query.limit(5000).all():
        text = crypto_service.decrypt(doc.text_encrypted)
        sent_label = doc.analysis.sentiment_label if doc.analysis else ""
        sent_score = doc.analysis.sentiment_score if doc.analysis else ""
        intent = doc.analysis.intent if doc.analysis else ""
        intent_score = doc.analysis.intent_score if doc.analysis else ""
        low_conf = doc.analysis.low_confidence if doc.analysis else ""
        writer.writerow([
            doc.id,
            text,
            doc.label or "",
            doc.timestamp.isoformat() if doc.timestamp else "",
            sent_label,
            sent_score,
            intent,
            intent_score,
            low_conf
        ])
    return output.getvalue()

def generate_html_report(
    db: Session,
    dataset_id: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
) -> str:
    summary = get_dashboard_summary(db, dataset_id=dataset_id, start_date=start_date, end_date=end_date)
    timestamp_str = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

    sentiment_rows = "".join(
        f"<tr><td>{k}</td><td>{v}%</td></tr>"
        for k, v in summary["sentiment_distribution"].items()
    ) or "<tr><td colspan='2'>No sentiment data available</td></tr>"

    label_rows = "".join(
        f"<tr><td>{k}</td><td>{v}%</td></tr>"
        for k, v in summary["label_distribution"].items()
    ) or "<tr><td colspan='2'>No category data available</td></tr>"

    topic_rows = "".join(
        f"<tr><td>{t['name']}</td><td>{t['percentage']}%</td><td>{t['count']}</td></tr>"
        for t in summary["topic_sizes"]
    ) or "<tr><td colspan='3'>No topic clusters available</td></tr>"

    findings_items = "".join(
        f"<li>{finding}</li>"
        for finding in summary["key_findings"]
    )

    f1_display = f"{summary['deployed_model_f1']:.2f}" if summary['deployed_model_f1'] else "N/A"

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>InsightText Executive Analysis Report</title>
<style>
  body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; margin: 40px; background: #0f172a; color: #f8fafc; }}
  h1 {{ color: #38bdf8; font-size: 24px; margin-bottom: 4px; }}
  .meta {{ color: #94a3b8; font-size: 14px; margin-bottom: 30px; }}
  .cards {{ display: flex; gap: 20px; margin-bottom: 30px; }}
  .card {{ background: #1e293b; border: 1px solid #334155; border-radius: 8px; padding: 20px; flex: 1; }}
  .card-val {{ font-size: 28px; font-weight: bold; margin-top: 8px; color: #f1f5f9; }}
  .section {{ background: #1e293b; border: 1px solid #334155; border-radius: 8px; padding: 20px; margin-bottom: 24px; }}
  table {{ width: 100%; border-collapse: collapse; margin-top: 12px; }}
  th, td {{ text-align: left; padding: 10px 12px; border-bottom: 1px solid #334155; }}
  th {{ color: #94a3b8; font-size: 13px; text-transform: uppercase; }}
  ul {{ padding-left: 20px; line-height: 1.8; }}
</style>
</head>
<body>
  <h1>InsightText Analysis Report</h1>
  <div class="meta">Generated: {timestamp_str}</div>
  <div class="cards">
    <div class="card"><div>Documents Processed</div><div class="card-val">{summary['documents_processed']:,}</div></div>
    <div class="card"><div>Datasets</div><div class="card-val">{summary['datasets_count']}</div></div>
    <div class="card"><div>Deployed Model F1</div><div class="card-val">{f1_display}</div></div>
    <div class="card"><div>Predictions Today</div><div class="card-val">{summary['predictions_today']:,}</div></div>
  </div>
  <div class="section">
    <h2>Sentiment Distribution</h2>
    <table><thead><tr><th>Sentiment</th><th>Share</th></tr></thead><tbody>{sentiment_rows}</tbody></table>
  </div>
  <div class="section">
    <h2>Category Breakdown</h2>
    <table><thead><tr><th>Category</th><th>Share</th></tr></thead><tbody>{label_rows}</tbody></table>
  </div>
  <div class="section">
    <h2>Top Topics</h2>
    <table><thead><tr><th>Topic</th><th>Share</th><th>Count</th></tr></thead><tbody>{topic_rows}</tbody></table>
  </div>
  <div class="section">
    <h2>Key Findings</h2>
    <ul>
      {findings_items}
    </ul>
  </div>
</body>
</html>"""
