"""
Demo data simulator.

Generates realistic-looking banking transactions including intentionally
suspicious patterns (large amounts, high-frequency bursts, odd-hours activity)
to exercise all alert rules.
"""

from __future__ import annotations

import random
import uuid
from datetime import datetime, timedelta
from typing import List

from models import Transaction, TransactionType

MERCHANTS = [
    "Amazon", "Walmart", "Apple Store", "Netflix", "Uber", "Airbnb",
    "Shell", "Starbucks", "Best Buy", "Chase ATM", "Wire Transfer",
    "PayPal", "Stripe", "Square", "HSBC Wire",
]

ACCOUNT_IDS = [f"ACC{str(i).zfill(4)}" for i in range(1, 21)]  # 20 accounts


def _rand_tx(
    account_id: str,
    ts: datetime,
    amount: float | None = None,
    tx_type: TransactionType | None = None,
) -> Transaction:
    return Transaction(
        transaction_id=str(uuid.uuid4()),
        account_id=account_id,
        amount=amount or round(random.uniform(5.0, 2000.0), 2),
        currency="USD",
        transaction_type=tx_type or random.choice(list(TransactionType)),
        merchant=random.choice(MERCHANTS),
        description="Simulated transaction",
        timestamp=ts,
    )


def generate_transactions(n_normal: int = 200) -> List[Transaction]:
    """
    Return a mixed list of normal + suspicious transactions.
    Suspicious patterns injected:
      • 3 large transactions (>= $10,000)
      • 1 high-frequency burst (15 tx from same account in 30 min)
      • 1 large-volume day (>= $50,000 across multiple tx)
      • 5 odd-hour transactions (01:00–04:00)
    """
    txs: List[Transaction] = []
    now = datetime.utcnow()

    # ── Normal transactions ───────────────────────────────────────────────
    for _ in range(n_normal):
        ts = now - timedelta(
            days=random.randint(0, 7),
            hours=random.randint(6, 23),
            minutes=random.randint(0, 59),
        )
        txs.append(_rand_tx(random.choice(ACCOUNT_IDS), ts))

    # ── Large single transactions ─────────────────────────────────────────
    for _ in range(3):
        ts = now - timedelta(days=random.randint(0, 3), hours=random.randint(9, 18))
        txs.append(_rand_tx(
            random.choice(ACCOUNT_IDS), ts,
            amount=round(random.uniform(10_000, 75_000), 2),
            tx_type=TransactionType.transfer,
        ))

    # ── High-frequency burst ──────────────────────────────────────────────
    burst_account = "ACC0001"
    burst_start = now - timedelta(hours=2)
    for i in range(15):
        ts = burst_start + timedelta(minutes=i * 2)
        txs.append(_rand_tx(burst_account, ts, amount=round(random.uniform(50, 500), 2)))

    # ── High cumulative volume day ────────────────────────────────────────
    volume_account = "ACC0002"
    volume_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
    for i in range(8):
        ts = volume_day + timedelta(hours=i + 9, minutes=random.randint(0, 59))
        txs.append(_rand_tx(
            volume_account, ts,
            amount=round(random.uniform(7_000, 9_000), 2),
            tx_type=TransactionType.payment,
        ))

    # ── Odd-hour transactions ─────────────────────────────────────────────
    for _ in range(5):
        ts = now - timedelta(
            days=random.randint(0, 5),
            hours=0,
            minutes=random.randint(0, 239),  # maps to 00:00–03:59
        )
        ts = ts.replace(hour=random.randint(0, 4))
        txs.append(_rand_tx(random.choice(ACCOUNT_IDS), ts))

    # Sort chronologically
    txs.sort(key=lambda t: t.timestamp)
    return txs
