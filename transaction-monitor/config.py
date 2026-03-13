"""
Transaction Monitoring App — Configuration
All alert thresholds and system settings are centralised here.
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # ── App ────────────────────────────────────────────────────────────────
    app_title: str = "Transaction Monitor"
    app_version: str = "1.0.0"
    database_url: str = "sqlite:///./transactions.db"

    # ── Velocity rule: high-frequency ─────────────────────────────────────
    # Flag if an account makes more than N transactions within M minutes
    frequency_max_tx: int = 10          # maximum allowed transactions …
    frequency_window_minutes: int = 60  # … within this rolling window

    # ── Volume rule: large single transaction ─────────────────────────────
    large_tx_threshold: float = 10_000.0   # USD (or equivalent)

    # ── Volume rule: high cumulative daily spend ───────────────────────────
    daily_volume_threshold: float = 50_000.0  # per account per calendar day

    # ── Time-of-day rule ───────────────────────────────────────────────────
    unusual_hour_start: int = 0   # midnight  (inclusive)
    unusual_hour_end: int = 5     # 05:00 AM  (exclusive)

    # ── Reporting ──────────────────────────────────────────────────────────
    reports_dir: str = "reports"
    log_file: str = "transaction_monitor.log"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
