"""
SQLAlchemy ORM models + Pydantic schemas.
"""

from __future__ import annotations

import enum
from datetime import datetime

from sqlalchemy import (
    Column, DateTime, Enum, Float, ForeignKey,
    Integer, String, Text, create_engine,
)
from sqlalchemy.orm import DeclarativeBase, relationship, sessionmaker

from config import settings

# ── Database setup ────────────────────────────────────────────────────────────

engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False},
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


# ── Enums ─────────────────────────────────────────────────────────────────────

class TransactionType(str, enum.Enum):
    debit = "debit"
    credit = "credit"
    transfer = "transfer"
    payment = "payment"
    withdrawal = "withdrawal"


class AlertRule(str, enum.Enum):
    high_frequency = "HIGH_FREQUENCY"
    large_transaction = "LARGE_TRANSACTION"
    high_daily_volume = "HIGH_DAILY_VOLUME"
    unusual_hours = "UNUSUAL_HOURS"


# ── ORM models ────────────────────────────────────────────────────────────────

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    transaction_id = Column(String(64), unique=True, index=True, nullable=False)
    account_id = Column(String(64), index=True, nullable=False)
    amount = Column(Float, nullable=False)
    currency = Column(String(8), default="USD")
    transaction_type = Column(Enum(TransactionType), nullable=False)
    merchant = Column(String(128), nullable=True)
    description = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    alerts = relationship("Alert", back_populates="transaction", cascade="all, delete-orphan")


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    transaction_id_fk = Column(Integer, ForeignKey("transactions.id"), nullable=False)
    rule = Column(Enum(AlertRule), nullable=False)
    detail = Column(Text, nullable=False)
    flagged_at = Column(DateTime, default=datetime.utcnow)

    transaction = relationship("Transaction", back_populates="alerts")


def create_tables():
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
