from datetime import datetime
from typing import Optional, Any
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.db import get_db
from app.core.deps import get_current_user_or_api_key, record_audit_log
from app.core.errors import AppException
from app.models.all_models import User, Dataset, Document
from app.schemas.all_schemas import IngestPayload, DatasetResponse
from app.services.crypto import crypto_service
from app.api.datasets import parse_date

router = APIRouter(prefix="/ingest", tags=["ingest"])

@router.post("", response_model=DatasetResponse, status_code=status.HTTP_201_CREATED)
def ingest_data(
    payload: IngestPayload,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_or_api_key)
):
    if not payload.records:
        raise AppException(status.HTTP_400_BAD_REQUEST, "EMPTY_PAYLOAD", "Payload must contain at least one record")

    if len(payload.records) > 50000:
        raise AppException(status.HTTP_400_BAD_REQUEST, "LIMIT_EXCEEDED", "Maximum 50,000 records allowed per ingest")

    text_col = payload.text_column
    first_record = payload.records[0]
    if text_col not in first_record:
        raise AppException(
            status.HTTP_400_BAD_REQUEST,
            "MISSING_TEXT_COLUMN",
            f"Specified text column '{text_col}' not found in record fields: {list(first_record.keys())}"
        )

    user_id = current_user.id if current_user else None

    dataset = Dataset(
        name=payload.name or f"API Ingest {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}",
        owner_id=user_id,
        source="api",
        row_count=len(payload.records),
        text_column=text_col,
        label_column=payload.label_column,
        time_column=payload.time_column,
        status="ready"
    )
    db.add(dataset)
    db.commit()
    db.refresh(dataset)

    doc_objects = []
    for row in payload.records:
        raw_text = str(row.get(text_col, ""))
        lbl = str(row.get(payload.label_column)) if payload.label_column and row.get(payload.label_column) else None
        dt = parse_date(row.get(payload.time_column)) if payload.time_column else None
        
        doc = Document(
            dataset_id=dataset.id,
            text_encrypted=crypto_service.encrypt(raw_text),
            label=lbl,
            timestamp=dt,
            meta={k: v for k, v in row.items() if k not in [text_col, payload.label_column, payload.time_column]},
            processed=False
        )
        doc_objects.append(doc)

    db.bulk_save_objects(doc_objects)
    db.commit()

    record_audit_log(db, user_id, "API_INGEST", {
        "dataset_id": dataset.id,
        "name": dataset.name,
        "rows": len(doc_objects)
    })

    return dataset
