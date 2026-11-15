from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import numpy as np
from sqlalchemy.orm import Session
from sqlalchemy import func
from xgboost import XGBRegressor
from app.models.all_models import Document, Analysis

def forecast_series(values: List[float], periods: int = 7) -> List[float]:
    if not values:
        return [0.0] * periods
    
    if len(values) < 5:
        window = min(3, len(values))
        avg = float(np.mean(values[-window:]))
        step = (values[-1] - values[0]) / max(1, len(values) - 1) * 0.2
        return [round(float(np.clip(avg + (i + 1) * step, 0.0, 1.0)), 4) for i in range(periods)]

    lags = min(3, len(values) - 2)
    X, y = [], []
    for i in range(lags, len(values)):
        X.append(values[i-lags:i])
        y.append(values[i])

    X = np.array(X)
    y = np.array(y)

    model = XGBRegressor(n_estimators=35, max_depth=2, learning_rate=0.08, random_state=42)
    model.fit(X, y)

    current_window = list(values[-lags:])
    forecasts = []
    for _ in range(periods):
        feat = np.array([current_window[-lags:]])
        pred = float(model.predict(feat)[0])
        pred = float(np.clip(pred, 0.0, 1.0))
        forecasts.append(round(pred, 4))
        current_window.append(pred)

    return forecasts

def compute_trend_forecast(
    db: Session,
    dataset_id: Optional[str] = None,
    target: str = "negative_sentiment",
    periods: int = 7,
    period_type: str = "day"
) -> Dict[str, Any]:
    query = db.query(Document).filter(Document.timestamp.isnot(None))
    if dataset_id:
        query = query.filter(Document.dataset_id == dataset_id)

    docs = query.order_by(Document.timestamp.asc()).all()

    points_by_date: Dict[str, List[float]] = {}
    
    for doc in docs:
        d_str = doc.timestamp.strftime("%Y-%m-%d")
        val = 0.0
        if doc.analysis:
            if target in ["negative", "negative_sentiment"]:
                val = 1.0 if doc.analysis.sentiment_label.lower() == "negative" else 0.0
            elif target in ["positive", "positive_sentiment"]:
                val = 1.0 if doc.analysis.sentiment_label.lower() == "positive" else 0.0
            else:
                val = 1.0 if doc.analysis.sentiment_label.lower() == "negative" else 0.0
        else:
            val = 0.2
        
        if d_str not in points_by_date:
            points_by_date[d_str] = []
        points_by_date[d_str].append(val)

    if not points_by_date:
        today = datetime.utcnow()
        points_by_date = {}
        for i in range(14, 0, -1):
            dt = today - timedelta(days=i)
            base_val = 0.18 + 0.01 * (14 - i) + (0.02 if i % 3 == 0 else -0.01)
            points_by_date[dt.strftime("%Y-%m-%d")] = [base_val]

    sorted_dates = sorted(points_by_date.keys())
    historical_points = []
    historical_values = []

    for d in sorted_dates:
        avg_val = round(float(np.mean(points_by_date[d])), 4)
        historical_values.append(avg_val)
        historical_points.append({
            "date": d,
            "actual": avg_val,
            "forecast": None,
            "is_forecast": False
        })

    forecast_values = forecast_series(historical_values, periods=periods)
    
    last_dt = datetime.strptime(sorted_dates[-1], "%Y-%m-%d")
    forecast_points = []
    
    if historical_points:
        historical_points[-1]["forecast"] = historical_points[-1]["actual"]

    for i, f_val in enumerate(forecast_values):
        next_dt = last_dt + timedelta(days=i+1)
        forecast_points.append({
            "date": next_dt.strftime("%Y-%m-%d"),
            "actual": None,
            "forecast": f_val,
            "is_forecast": True
        })

    last_actual = historical_values[-1] if historical_values else 0.2
    final_forecast = forecast_values[-1] if forecast_values else last_actual
    change_pct = round(((final_forecast - last_actual) / max(0.01, last_actual)) * 100, 1)

    direction = "rise" if change_pct >= 0 else "drop"
    summary_text = f"Dashed line shows forecast. Expected {direction} of {abs(change_pct)}% over the next period."

    return {
        "target": target,
        "points": historical_points + forecast_points,
        "summary_change_pct": change_pct,
        "summary_text": summary_text
    }
