"""
Report generation utilities.

Exports:
  • CSV of all flagged transactions
  • JSON summary report
  • Plain-text log entries
"""

from __future__ import annotations

import csv
import json
import logging
import os
from datetime import datetime
from typing import List

from sqlalchemy.orm import Session

from config import settings
from models import Alert, Transaction

# ── Logger ────────────────────────────────────────────────────────────────────

os.makedirs(settings.reports_dir, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[
        logging.FileHandler(settings.log_file),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger("transaction_monitor")


# ── Helpers ───────────────────────────────────────────────────────────────────

def log_alert(alert: Alert, tx: Transaction):
    logger.warning(
        "ALERT [%s] tx=%s account=%s amount=%.2f %s | %s",
        alert.rule.value,
        tx.transaction_id,
        tx.account_id,
        tx.amount,
        tx.currency,
        alert.detail,
    )


def log_info(msg: str):
    logger.info(msg)


# ── CSV export ────────────────────────────────────────────────────────────────

def export_flagged_csv(db: Session, filename: str | None = None) -> str:
    """Write all alerted transactions to a CSV file and return the path."""
    if not filename:
        ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = os.path.join(settings.reports_dir, f"flagged_transactions_{ts}.csv")

    alerts: List[Alert] = db.query(Alert).all()

    rows = []
    seen_tx_ids = set()
    for alert in alerts:
        tx = alert.transaction
        key = (tx.transaction_id, alert.rule.value)
        if key in seen_tx_ids:
            continue
        seen_tx_ids.add(key)
        rows.append({
            "transaction_id": tx.transaction_id,
            "account_id": tx.account_id,
            "amount": tx.amount,
            "currency": tx.currency,
            "type": tx.transaction_type.value,
            "merchant": tx.merchant or "",
            "timestamp": tx.timestamp.isoformat(),
            "alert_rule": alert.rule.value,
            "alert_detail": alert.detail,
            "flagged_at": alert.flagged_at.isoformat(),
        })

    fieldnames = [
        "transaction_id", "account_id", "amount", "currency", "type",
        "merchant", "timestamp", "alert_rule", "alert_detail", "flagged_at",
    ]

    with open(filename, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    logger.info("CSV report written: %s (%d rows)", filename, len(rows))
    return filename


# ── JSON summary ──────────────────────────────────────────────────────────────

def generate_summary(db: Session) -> dict:
    total_tx = db.query(Transaction).count()
    total_alerts = db.query(Alert).count()
    flagged_accounts = (
        db.query(Transaction.account_id)
        .join(Alert, Alert.transaction_id_fk == Transaction.id)
        .distinct()
        .count()
    )

    rule_counts: dict[str, int] = {}
    for alert in db.query(Alert).all():
        rule_counts[alert.rule.value] = rule_counts.get(alert.rule.value, 0) + 1

    return {
        "generated_at": datetime.utcnow().isoformat(),
        "total_transactions": total_tx,
        "total_alerts": total_alerts,
        "flagged_accounts": flagged_accounts,
        "alerts_by_rule": rule_counts,
    }


def export_summary_json(db: Session, filename: str | None = None) -> str:
    if not filename:
        ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = os.path.join(settings.reports_dir, f"summary_{ts}.json")

    summary = generate_summary(db)
    with open(filename, "w") as f:
        json.dump(summary, f, indent=2)

    logger.info("JSON summary written: %s", filename)
    return filename
