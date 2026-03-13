"""
Alert rule engine.

Each rule function receives the newly inserted Transaction ORM object plus
an active SQLAlchemy session and returns a (possibly empty) list of Alert
objects to be persisted.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import List

from sqlalchemy.orm import Session

from config import settings
from models import Alert, AlertRule, Transaction


def _make_alert(tx: Transaction, rule: AlertRule, detail: str) -> Alert:
    return Alert(
        transaction_id_fk=tx.id,
        rule=rule,
        detail=detail,
    )


# ── Rule 1: Large single transaction ─────────────────────────────────────────

def rule_large_transaction(tx: Transaction, _db: Session) -> List[Alert]:
    if tx.amount >= settings.large_tx_threshold:
        return [
            _make_alert(
                tx,
                AlertRule.large_transaction,
                f"Transaction amount {tx.currency} {tx.amount:,.2f} exceeds "
                f"threshold of {tx.currency} {settings.large_tx_threshold:,.2f}.",
            )
        ]
    return []


# ── Rule 2: High cumulative daily volume ──────────────────────────────────────

def rule_high_daily_volume(tx: Transaction, db: Session) -> List[Alert]:
    day_start = tx.timestamp.replace(hour=0, minute=0, second=0, microsecond=0)
    day_end = day_start + timedelta(days=1)

    result = (
        db.query(Transaction)
        .filter(
            Transaction.account_id == tx.account_id,
            Transaction.timestamp >= day_start,
            Transaction.timestamp < day_end,
        )
        .all()
    )
    daily_total = sum(t.amount for t in result)

    if daily_total >= settings.daily_volume_threshold:
        return [
            _make_alert(
                tx,
                AlertRule.high_daily_volume,
                f"Account {tx.account_id} cumulative daily volume "
                f"{tx.currency} {daily_total:,.2f} exceeds threshold of "
                f"{tx.currency} {settings.daily_volume_threshold:,.2f}.",
            )
        ]
    return []


# ── Rule 3: High transaction frequency ───────────────────────────────────────

def rule_high_frequency(tx: Transaction, db: Session) -> List[Alert]:
    window_start = tx.timestamp - timedelta(minutes=settings.frequency_window_minutes)

    count = (
        db.query(Transaction)
        .filter(
            Transaction.account_id == tx.account_id,
            Transaction.timestamp >= window_start,
            Transaction.timestamp <= tx.timestamp,
        )
        .count()
    )

    if count > settings.frequency_max_tx:
        return [
            _make_alert(
                tx,
                AlertRule.high_frequency,
                f"Account {tx.account_id} made {count} transactions in the last "
                f"{settings.frequency_window_minutes} minutes "
                f"(limit: {settings.frequency_max_tx}).",
            )
        ]
    return []


# ── Rule 4: Unusual time-of-day ───────────────────────────────────────────────

def rule_unusual_hours(tx: Transaction, _db: Session) -> List[Alert]:
    hour = tx.timestamp.hour
    start = settings.unusual_hour_start
    end = settings.unusual_hour_end

    if start <= hour < end:
        return [
            _make_alert(
                tx,
                AlertRule.unusual_hours,
                f"Transaction occurred at {tx.timestamp.strftime('%H:%M UTC')} "
                f"which is within the unusual hours window "
                f"({start:02d}:00 – {end:02d}:00 UTC).",
            )
        ]
    return []


# ── Engine entry point ────────────────────────────────────────────────────────

RULES = [
    rule_large_transaction,
    rule_high_daily_volume,
    rule_high_frequency,
    rule_unusual_hours,
]


def evaluate(tx: Transaction, db: Session) -> List[Alert]:
    """Run all rules against a transaction and return generated alerts."""
    alerts: List[Alert] = []
    for rule_fn in RULES:
        alerts.extend(rule_fn(tx, db))
    return alerts
