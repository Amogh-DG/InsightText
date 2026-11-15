import os
import json
import csv
import io
from datetime import datetime
from typing import List, Optional, Any
from fastapi import APIRouter, Depends, UploadFile, File, Form, status, Response
from sqlalchemy.orm import Session
from app.db import get_db
from app.config import settings
from app.core.rbac import require_roles
from app.core.deps import get_current_user, record_audit_log
from app.core.errors import AppException
from app.models.all_models import User, Dataset, Document
from app.schemas.all_schemas import DatasetResponse, DatasetPreviewResponse
from app.services.crypto import crypto_service

router = APIRouter(prefix="/datasets", tags=["datasets"])

def parse_date(date_str: Any) -> Optional[datetime]:
    if not date_str:
        return None
    date_str = str(date_str).strip()
    formats = [
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d",
        "%d/%m/%Y",
        "%m/%d/%Y",
        "%d-%m-%Y"
    ]
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            pass
    return None

def read_file_records(file_bytes: bytes, filename: str) -> tuple[List[str], List[dict]]:
    ext = os.path.splitext(filename)[1].lower()
    
    if ext == ".xlsx":
        import openpyxl
        wb = openpyxl.load_workbook(io.BytesIO(file_bytes), data_only=True)
        sheet = wb.active
        rows = list(sheet.iter_rows(values_only=True))
        if not rows:
            return [], []
        columns = [str(c).strip() if c is not None else f"col_{i}" for i, c in enumerate(rows[0])]
        records = []
        for r in rows[1:]:
            if all(v is None for v in r):
                continue
            row_dict = {}
            for col_name, val in zip(columns, r):
                row_dict[col_name] = str(val) if val is not None else ""
            records.append(row_dict)
        return columns, records
    
    text_content = file_bytes.decode("utf-8", errors="replace")
    
    if ext == ".json":
        data = json.loads(text_content)
        if isinstance(data, list):
            records = data
        elif isinstance(data, dict):
            records = data.get("records") or data.get("data") or [data]
        else:
            records = []
        columns = list(records[0].keys()) if records else []
        return columns, records
    
    elif ext in [".csv", ".txt"]:
        f = io.StringIO(text_content)
        reader = csv.DictReader(f)
        columns = reader.fieldnames or []
        records = list(reader)
        return list(columns), records
    
    else:
        raise AppException(
            status.HTTP_400_BAD_REQUEST,
            "UNSUPPORTED_FILE_TYPE",
            f"Unsupported file format '{ext}'. Accepted formats: CSV, XLSX, JSON, TXT"
        )

@router.post("/preview", response_model=DatasetPreviewResponse)
async def preview_uploaded_file(
    file: UploadFile = File(...),
    current_user: User = Depends(require_roles("analyst", "data_scientist"))
):
    content = await file.read()
    if len(content) > 20 * 1024 * 1024:
        raise AppException(status.HTTP_400_BAD_REQUEST, "FILE_TOO_LARGE", "File size exceeds 20 MB limit")
    
    columns, records = read_file_records(content, file.filename)
    if not records:
        raise AppException(status.HTTP_400_BAD_REQUEST, "EMPTY_FILE", "The uploaded file contains no data")
    
    preview_rows = records[:10]
    return {
        "columns": columns,
        "rows": preview_rows,
        "total_rows": len(records)
    }

@router.post("/upload", response_model=DatasetResponse, status_code=status.HTTP_201_CREATED)
async def upload_dataset(
    file: UploadFile = File(...),
    name: str = Form(...),
    text_column: str = Form(...),
    label_column: Optional[str] = Form(None),
    time_column: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("analyst", "data_scientist"))
):
    content = await file.read()
    if len(content) > 20 * 1024 * 1024:
        raise AppException(status.HTTP_400_BAD_REQUEST, "FILE_TOO_LARGE", "File size exceeds 20 MB limit")

    columns, records = read_file_records(content, file.filename)
    if not records:
        raise AppException(status.HTTP_400_BAD_REQUEST, "EMPTY_FILE", "The uploaded file contains no records")
    
    if len(records) > 50000:
        raise AppException(status.HTTP_400_BAD_REQUEST, "ROW_LIMIT_EXCEEDED", "Maximum 50,000 rows permitted")

    if text_column not in columns:
        raise AppException(
            status.HTTP_400_BAD_REQUEST,
            "INVALID_COLUMN_MAPPING",
            f"Selected text column '{text_column}' was not found in file columns: {columns}"
        )

    errors = []
    for idx, row in enumerate(records[:1000]):
        row_num = idx + 1
        raw_text = row.get(text_column)
        if not raw_text or not str(raw_text).strip():
            errors.append({"row": f"Row {row_num}", "problem": "Text column is empty"})
        
        if time_column and row.get(time_column):
            dt = parse_date(row.get(time_column))
            if dt is None:
                errors.append({"row": f"Row {row_num}", "problem": f"Date '{row.get(time_column)}' is not a valid date"})

    if len(errors) > 0:
        raise AppException(
            status.HTTP_400_BAD_REQUEST,
            "IMPORT_FAILED",
            f"File import failed with {len(errors)} validation errors. Check column mappings and data values.",
            details=errors
        )

    dataset = Dataset(
        name=name,
        owner_id=current_user.id,
        source="upload",
        row_count=len(records),
        text_column=text_column,
        label_column=label_column if label_column in columns else None,
        time_column=time_column if time_column in columns else None,
        status="ready"
    )
    db.add(dataset)
    db.commit()
    db.refresh(dataset)

    doc_objects = []
    for row in records:
        raw_text = str(row.get(text_column, ""))
        lbl = str(row.get(label_column)) if label_column and row.get(label_column) else None
        dt = parse_date(row.get(time_column)) if time_column else None
        
        doc = Document(
            dataset_id=dataset.id,
            text_encrypted=crypto_service.encrypt(raw_text),
            label=lbl,
            timestamp=dt,
            meta={k: v for k, v in row.items() if k not in [text_column, label_column, time_column]},
            processed=False
        )
        doc_objects.append(doc)

    db.bulk_save_objects(doc_objects)
    db.commit()

    record_audit_log(db, current_user.id, "UPLOAD_DATASET", {
        "dataset_id": dataset.id,
        "name": dataset.name,
        "rows": len(doc_objects)
    })

    return dataset

@router.post("/error-report")
def download_error_report(
    errors: List[dict],
    current_user: User = Depends(require_roles("analyst", "data_scientist"))
):
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=["row", "problem"])
    writer.writeheader()
    for err in errors:
        writer.writerow({"row": err.get("row", ""), "problem": err.get("problem", "")})
    
    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=upload_validation_errors.csv"}
    )

@router.get("", response_model=List[DatasetResponse])
def list_datasets(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return db.query(Dataset).order_by(Dataset.created_at.desc()).all()

@router.get("/{dataset_id}", response_model=DatasetResponse)
def get_dataset(
    dataset_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise AppException(status.HTTP_404_NOT_FOUND, "DATASET_NOT_FOUND", "Dataset not found")
    return dataset

@router.get("/{dataset_id}/preview", response_model=DatasetPreviewResponse)
def preview_dataset(
    dataset_id: str,
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise AppException(status.HTTP_404_NOT_FOUND, "DATASET_NOT_FOUND", "Dataset not found")
    
    docs = db.query(Document).filter(Document.dataset_id == dataset_id).limit(limit).all()
    rows = []
    for doc in docs:
        row_data = {
            dataset.text_column: crypto_service.decrypt(doc.text_encrypted)
        }
        if dataset.label_column:
            row_data[dataset.label_column] = doc.label
        if dataset.time_column and doc.timestamp:
            row_data[dataset.time_column] = doc.timestamp.strftime("%Y-%m-%d")
        row_data.update(doc.meta)
        rows.append(row_data)

    cols = [dataset.text_column]
    if dataset.label_column:
        cols.append(dataset.label_column)
    if dataset.time_column:
        cols.append(dataset.time_column)

    return {
        "columns": cols,
        "rows": rows,
        "total_rows": dataset.row_count
    }

@router.delete("/{dataset_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_dataset(
    dataset_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("analyst", "data_scientist"))
):
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise AppException(status.HTTP_404_NOT_FOUND, "DATASET_NOT_FOUND", "Dataset not found")
    
    db.delete(dataset)
    db.commit()
    record_audit_log(db, current_user.id, "DELETE_DATASET", {"dataset_id": dataset_id, "name": dataset.name})
    return None
