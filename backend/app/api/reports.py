from typing import Optional
from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session
from app.db import get_db
from app.core.deps import get_current_user
from app.schemas.all_schemas import DashboardSummary
from app.services.reports import get_dashboard_summary, generate_csv_report, generate_html_report
from app.models.all_models import User

router = APIRouter(prefix="/reports", tags=["reports"])

@router.get("/summary", response_model=DashboardSummary)
def get_reports_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return get_dashboard_summary(db)

@router.get("/export")
def export_reports(
    format: str = Query("csv", pattern="^(csv|html)$"),
    dataset_id: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if format == "html":
        content = generate_html_report(db, dataset_id=dataset_id)
        return Response(content=content, media_type="text/html", headers={
            "Content-Disposition": f"attachment; filename=insighttext_report_{dataset_id or 'global'}.html"
        })
    else:
        content = generate_csv_report(db, dataset_id=dataset_id)
        return Response(content=content, media_type="text/csv", headers={
            "Content-Disposition": f"attachment; filename=insighttext_data_{dataset_id or 'all'}.csv"
        })
