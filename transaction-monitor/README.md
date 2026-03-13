# Transaction Monitor

A financial transaction monitoring app built with **Python + FastAPI**.
Detects suspicious activity using velocity and volume-based alert rules and surfaces findings on a real-time dashboard.

---

## Features

| Feature | Description |
|---|---|
| **Large Transaction** | Flags any single transaction above a configurable threshold (default $10,000) |
| **High Frequency** | Flags accounts that exceed N transactions within a rolling time window (default: 10 in 60 min) |
| **High Daily Volume** | Flags accounts whose cumulative spend in a calendar day exceeds a limit (default $50,000) |
| **Unusual Hours** | Flags transactions occurring in the early-morning window (default 00:00–05:00 UTC) |
| **CSV Upload** | Ingest transactions from a CSV file |
| **Demo Data** | One-click load of realistic simulated data with embedded suspicious patterns |
| **Dashboard** | Live charts, alert table, transaction table, pagination, filters |
| **Reports** | Export flagged transactions to CSV; export JSON summary |
| **Runtime Config** | Adjust all thresholds via the UI without restarting the server |

---

## Quick Start

```bash
cd transaction-monitor

# 1. Install dependencies
pip install -r requirements.txt

# 2. Start the server
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# 3. Open the dashboard
# http://localhost:8000
```

Then click **"Load Demo Data"** to populate the system with test transactions and see alerts fire.

---

## CSV Upload Format

| Column | Required | Notes |
|---|---|---|
| `transaction_id` | No | Auto-generated UUID if omitted |
| `account_id` | **Yes** | |
| `amount` | **Yes** | Positive number |
| `currency` | No | Defaults to `USD` |
| `transaction_type` | **Yes** | `debit`, `credit`, `transfer`, `payment`, `withdrawal` |
| `merchant` | No | |
| `description` | No | |
| `timestamp` | No | ISO 8601 (`2026-03-10T14:30:00`). Defaults to now |

See `sample_data/sample_transactions.csv` for an example.

---

## API Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/stats` | Summary statistics |
| `GET` | `/api/transactions` | List transactions (filters: `account_id`, `flagged_only`, `limit`, `offset`) |
| `POST` | `/api/transactions` | Create a single transaction |
| `GET` | `/api/alerts` | List alerts (filters: `rule`, `account_id`, `limit`, `offset`) |
| `POST` | `/api/upload` | Upload a CSV file |
| `POST` | `/api/simulate` | Load demo data (`?n_normal=200`) |
| `POST` | `/api/reports/csv` | Export flagged transactions to CSV |
| `POST` | `/api/reports/json` | Export summary to JSON |
| `GET` | `/api/config/thresholds` | Get current thresholds |
| `PUT` | `/api/config/thresholds` | Update thresholds |
| `DELETE` | `/api/data` | Wipe all data (dev use) |

Interactive docs: `http://localhost:8000/docs`

---

## Project Structure

```
transaction-monitor/
├── main.py               # FastAPI app & all routes
├── models.py             # SQLAlchemy ORM + Pydantic schemas
├── rules.py              # Alert rule engine
├── simulator.py          # Demo data generator
├── reports.py            # CSV/JSON report export + logging
├── config.py             # All thresholds and settings
├── requirements.txt
├── sample_data/
│   └── sample_transactions.csv
└── static/
    └── index.html        # Dashboard UI (Chart.js + vanilla JS)
```

---

## Configuration

Override defaults via environment variables or a `.env` file:

```env
LARGE_TX_THRESHOLD=10000
DAILY_VOLUME_THRESHOLD=50000
FREQUENCY_MAX_TX=10
FREQUENCY_WINDOW_MINUTES=60
UNUSUAL_HOUR_START=0
UNUSUAL_HOUR_END=5
```
