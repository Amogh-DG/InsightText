from app.services.crypto import crypto_service
from app.services.preprocess import clean_text, preprocess_text
from app.services.semantic import (
    analyze_single_text,
    analyze_sentiment,
    extract_entities,
    classify_intent,
    extract_topics
)
from app.services.classifier import load_model_bundle, predict_single, predict_many
from app.services.trainer import train_model_sync
from app.services.evaluator import evaluate_predictions
from app.services.predictor import predict_and_store, get_active_model
from app.services.trends import compute_trend_forecast
from app.services.reports import get_dashboard_summary, generate_csv_report, generate_html_report

__all__ = [
    "crypto_service",
    "clean_text",
    "preprocess_text",
    "analyze_single_text",
    "analyze_sentiment",
    "extract_entities",
    "classify_intent",
    "extract_topics",
    "load_model_bundle",
    "predict_single",
    "predict_many",
    "train_model_sync",
    "evaluate_predictions",
    "predict_and_store",
    "get_active_model",
    "compute_trend_forecast",
    "get_dashboard_summary",
    "generate_csv_report",
    "generate_html_report"
]
