from typing import List, Dict, Any
import numpy as np
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, classification_report, confusion_matrix
from app.config import settings

def evaluate_predictions(y_true: List[str], y_pred: List[str], labels: List[str]) -> Dict[str, Any]:
    acc = float(accuracy_score(y_true, y_pred))
    prec = float(precision_score(y_true, y_pred, average="macro", zero_division=0))
    rec = float(recall_score(y_true, y_pred, average="macro", zero_division=0))
    f1 = float(f1_score(y_true, y_pred, average="macro", zero_division=0))
    
    report_dict = classification_report(y_true, y_pred, labels=labels, output_dict=True, zero_division=0)
    per_class_report = {}
    for label in labels:
        if label in report_dict:
            per_class_report[label] = {
                "precision": round(float(report_dict[label]["precision"]), 4),
                "recall": round(float(report_dict[label]["recall"]), 4),
                "f1": round(float(report_dict[label]["f1-score"]), 4),
                "support": int(report_dict[label]["support"])
            }
        else:
            per_class_report[label] = {"precision": 0.0, "recall": 0.0, "f1": 0.0, "support": 0}

    cm = confusion_matrix(y_true, y_pred, labels=labels)
    cm_list = cm.tolist()
    
    target_met = f1 >= settings.TARGET_F1
    
    return {
        "accuracy": round(acc, 4),
        "precision": round(prec, 4),
        "recall": round(rec, 4),
        "f1": round(f1, 4),
        "target_f1_met": target_met,
        "per_class_report": per_class_report,
        "confusion_matrix": {
            "labels": labels,
            "matrix": cm_list
        }
    }
