"""
Transaction Monitoring App — FastAPI entry point.

Endpoints:
  GET  /                          → Serve dashboard UI
  GET  /api/stats                 → Summary statistics
  GET  /api/transactions          → List transactions (with filters)
  GET  /api/alerts                → List alerts (with filters)
  POST /api/upload                → Ingest CSV file
  POST /api/simulate              → Generate & load demo data
  POST /api/reports/csv           → Export flagged transactions CSV
  POST /api/reports/json          → Export summary JSON
  PUT  /api/config/thresholds     → Update alert thresholds at runtime
  GET  /api/config/thresholds     → Get current thresholds
  DELETE /api/data                → Wipe all data (dev use)
"""

from __future__ import annotations

import csv
import io
import uuid
from datetime import datetime
from typing import List, Optional

from fastapi import Depends, FastAPI, File, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from config import settings
from models import Alert, Transaction, TransactionType, create_tables, get_db
from reports import export_flagged_csv, export_summary_json, generate_summary, log_alert, log_info
from rules import evaluate
from simulator import generate_transactions

# ── App bootstrap ─────────────────────────────────────────────────────────────

create_tables()

app = FastAPI(title=settings.app_title, version=settings.app_version)
app.mount("/static", StaticFiles(directory="static"), name="static")


# ── Pydantic schemas ──────────────────────────────────────────────────────────

class TransactionIn(BaseModel):
    transaction_id: Optional[str] = None
    account_id: str
    amount: float = Field(..., gt=0)
    currency: str = "USD"
    transaction_type: TransactionType
    merchant: Optional[str] = None
    description: Optional[str] = None
    timestamp: Optional[datetime] = None


class ThresholdUpdate(BaseModel):
    large_tx_threshold: Optional[float] = None
    daily_volume_threshold: Optional[float] = None
    frequency_max_tx: Optional[int] = None
    frequency_window_minutes: Optional[int] = None
    unusual_hour_start: Optional[int] = None
    unusual_hour_end: Optional[int] = None


# ── Helpers ───────────────────────────────────────────────────────────────────

def _ingest_transaction(data: TransactionIn, db: Session) -> Transaction:
    tx = Transaction(
        transaction_id=data.transaction_id or str(uuid.uuid4()),
        account_id=data.account_id,
        amount=data.amount,
        currency=data.currency,
        transaction_type=data.transaction_type,
        merchant=data.merchant,
        description=data.description,
        timestamp=data.timestamp or datetime.utcnow(),
    )
    db.add(tx)
    db.flush()  # get tx.id before alert FK

    alerts = evaluate(tx, db)
    for alert in alerts:
        db.add(alert)
        log_alert(alert, tx)

    db.commit()
    db.refresh(tx)
    return tx


def _tx_to_dict(tx: Transaction) -> dict:
    return {
        "id": tx.id,
        "transaction_id": tx.transaction_id,
        "account_id": tx.account_id,
        "amount": tx.amount,
        "currency": tx.currency,
        "type": tx.transaction_type.value,
        "merchant": tx.merchant,
        "description": tx.description,
        "timestamp": tx.timestamp.isoformat(),
        "alert_count": len(tx.alerts),
        "flagged": len(tx.alerts) > 0,
    }


def _alert_to_dict(alert: Alert) -> dict:
    tx = alert.transaction
    return {
        "id": alert.id,
        "rule": alert.rule.value,
        "detail": alert.detail,
        "flagged_at": alert.flagged_at.isoformat(),
        "transaction": {
            "transaction_id": tx.transaction_id,
            "account_id": tx.account_id,
            "amount": tx.amount,
            "currency": tx.currency,
            "timestamp": tx.timestamp.isoformat(),
        },
    }


# ── Routes ────────────────────────────────────────────────────────────────────

@app.get("/", include_in_schema=False)
def serve_dashboard():
    return FileResponse("static/index.html")


# ── Stats ─────────────────────────────────────────────────────────────────────

@app.get("/api/stats")
def get_stats(db: Session = Depends(get_db)):
    return generate_summary(db)


# ── Transactions ──────────────────────────────────────────────────────────────

@app.get("/api/transactions")
def list_transactions(
    account_id: Optional[str] = Query(None),
    flagged_only: bool = Query(False),
    limit: int = Query(100, le=1000),
    offset: int = Query(0),
    db: Session = Depends(get_db),
):
    query = db.query(Transaction)
    if account_id:
        query = query.filter(Transaction.account_id == account_id)
    if flagged_only:
        query = query.join(Alert, Alert.transaction_id_fk == Transaction.id).distinct()
    query = query.order_by(Transaction.timestamp.desc())
    total = query.count()
    txs = query.offset(offset).limit(limit).all()
    return {"total": total, "transactions": [_tx_to_dict(t) for t in txs]}


@app.post("/api/transactions", status_code=201)
def create_transaction(data: TransactionIn, db: Session = Depends(get_db)):
    tx = _ingest_transaction(data, db)
    return _tx_to_dict(tx)


# ── Alerts ────────────────────────────────────────────────────────────────────

@app.get("/api/alerts")
def list_alerts(
    rule: Optional[str] = Query(None),
    account_id: Optional[str] = Query(None),
    limit: int = Query(100, le=1000),
    offset: int = Query(0),
    db: Session = Depends(get_db),
):
    query = db.query(Alert).join(Transaction, Alert.transaction_id_fk == Transaction.id)
    if rule:
        query = query.filter(Alert.rule == rule)
    if account_id:
        query = query.filter(Transaction.account_id == account_id)
    query = query.order_by(Alert.flagged_at.desc())
    total = query.count()
    alerts = query.offset(offset).limit(limit).all()
    return {"total": total, "alerts": [_alert_to_dict(a) for a in alerts]}


# ── CSV Upload ────────────────────────────────────────────────────────────────

@app.post("/api/upload")
async def upload_csv(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are accepted.")

    content = await file.read()
    reader = csv.DictReader(io.StringIO(content.decode("utf-8-sig")))

    required_fields = {"account_id", "amount", "transaction_type"}
    if not required_fields.issubset(set(reader.fieldnames or [])):
        raise HTTPException(
            status_code=400,
            detail=f"CSV must contain columns: {required_fields}. "
                   f"Found: {reader.fieldnames}",
        )

    ingested, flagged, errors = 0, 0, []
    for i, row in enumerate(reader, start=2):
        try:
            tx_type_raw = row.get("transaction_type", "").strip().lower()
            try:
                tx_type = TransactionType(tx_type_raw)
            except ValueError:
                tx_type = TransactionType.payment

            ts_raw = row.get("timestamp", "").strip()
            ts = datetime.fromisoformat(ts_raw) if ts_raw else datetime.utcnow()

            data = TransactionIn(
                transaction_id=row.get("transaction_id") or None,
                account_id=row["account_id"].strip(),
                amount=float(row["amount"]),
                currency=row.get("currency", "USD").strip() or "USD",
                transaction_type=tx_type,
                merchant=row.get("merchant") or None,
                description=row.get("description") or None,
                timestamp=ts,
            )
            tx = _ingest_transaction(data, db)
            ingested += 1
            if tx.alerts:
                flagged += 1
        except Exception as e:
            errors.append({"row": i, "error": str(e)})

    log_info(f"CSV upload complete: {ingested} ingested, {flagged} flagged, {len(errors)} errors")
    return {"ingested": ingested, "flagged": flagged, "errors": errors[:20]}


# ── Simulate ──────────────────────────────────────────────────────────────────

@app.post("/api/simulate")
def simulate(n_normal: int = Query(200, ge=10, le=2000), db: Session = Depends(get_db)):
    txs = generate_transactions(n_normal=n_normal)
    ingested, flagged = 0, 0
    for sim_tx in txs:
        # Persist directly (already have ORM objects from simulator)
        db.add(sim_tx)
        db.flush()
        alerts = evaluate(sim_tx, db)
        for alert in alerts:
            db.add(alert)
            log_alert(alert, sim_tx)
        if alerts:
            flagged += 1
        ingested += 1
    db.commit()
    log_info(f"Simulation complete: {ingested} transactions, {flagged} flagged")
    return {"ingested": ingested, "flagged": flagged}


# ── Reports ───────────────────────────────────────────────────────────────────

@app.post("/api/reports/csv")
def report_csv(db: Session = Depends(get_db)):
    path = export_flagged_csv(db)
    return {"file": path}


@app.post("/api/reports/json")
def report_json(db: Session = Depends(get_db)):
    path = export_summary_json(db)
    return {"file": path}


# ── Config ────────────────────────────────────────────────────────────────────

@app.get("/api/config/thresholds")
def get_thresholds():
    return {
        "large_tx_threshold": settings.large_tx_threshold,
        "daily_volume_threshold": settings.daily_volume_threshold,
        "frequency_max_tx": settings.frequency_max_tx,
        "frequency_window_minutes": settings.frequency_window_minutes,
        "unusual_hour_start": settings.unusual_hour_start,
        "unusual_hour_end": settings.unusual_hour_end,
    }


@app.put("/api/config/thresholds")
def update_thresholds(body: ThresholdUpdate):
    updated = {}
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(settings, field, value)
        updated[field] = value
    return {"updated": updated, "current": get_thresholds()}


# ── Dev: wipe data ────────────────────────────────────────────────────────────

@app.delete("/api/data")
def wipe_data(db: Session = Depends(get_db)):
    db.query(Alert).delete()
    db.query(Transaction).delete()
    db.commit()
    return {"status": "all data deleted"}
