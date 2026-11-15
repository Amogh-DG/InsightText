from typing import Optional
from datetime import datetime
from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session
from app.db import get_db
from app.core.deps import get_current_user
from app.schemas.all_schemas import DashboardSummary
from app.services.reports import get_dashboard_summary, generate_csv_report, generate_html_report
from app.models.all_models import User

router = APIRouter(prefix="/reports", tags=["reports"])

def parse_iso_date(dt_str: Optional[str]) -> Optional[datetime]:
    if not dt_str:
        return None
    try:
        return datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
    except Exception:
        for fmt in ("%Y-%m-%d", "%Y-%m-%d %H:%M:%S"):
            try:
                return datetime.strptime(dt_str, fmt)
            except Exception:
                pass
    return None

@router.get("/summary", response_model=DashboardSummary)
def get_reports_summary(
    dataset_id: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    st_dt = parse_iso_date(start_date)
    end_dt = parse_iso_date(end_date)
    return get_dashboard_summary(db, dataset_id=dataset_id, start_date=st_dt, end_date=end_dt)

@router.get("/export")
def export_reports(
    format: str = Query("csv", pattern="^(csv|html)$"),
    dataset_id: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    st_dt = parse_iso_date(start_date)
    end_dt = parse_iso_date(end_date)
    if format == "html":
        content = generate_html_report(db, dataset_id=dataset_id, start_date=st_dt, end_date=end_dt)
        return Response(content=content, media_type="text/html", headers={
            "Content-Disposition": f"attachment; filename=insighttext_report_{dataset_id or 'global'}.html"
        })
    else:
        content = generate_csv_report(db, dataset_id=dataset_id, start_date=st_dt, end_date=end_dt)
        return Response(content=content, media_type="text/csv", headers={
            "Content-Disposition": f"attachment; filename=insighttext_data_{dataset_id or 'all'}.csv"
        })
