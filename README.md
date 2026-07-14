# Live Expense Tracker with Anomaly Alerts

A containerized full-stack app where a user logs expenses, sees spending trends visualized, and gets flagged in near-real-time when an expense looks anomalous compared to their own history.

## Stack

| Layer             | Technology              |
| ----------------- | ----------------------- |
| Frontend          | React (Vite) + Recharts |
| Backend           | FastAPI                 |
| Anomaly Detection | Python (Rule-based)     |
| Database          | PostgreSQL 16           |
| Containerization  | Docker + Docker Compose |

## Architecture

```
┌─────────────┐      POST /api/expenses      ┌──────────────────┐
│   React     │ ───────────────────────────▶│  FastAPI (CRUD)  │
│  Dashboard  │                              │  writes to DB    │
│             │◀── GET /api/expenses ───────│                  │
│             │◀── GET /api/anomalies ──────│                  │
└─────────────┘                              └────────┬─────────┘
                                                      │
                                             BackgroundTasks (fire-and-forget)
                                                      ▼
                                             ┌──────────────────────┐
                                             │  Anomaly Detector    │
                                             │  (rule-based)        │
                                             │  writes to anomalies │
                                             │  table               │
                                             └──────────────────────┘
```

**Core principle:** Expense write success is never dependent on the anomaly service. The expense is saved to DB first, then detection runs async via FastAPI `BackgroundTasks`. If detection fails, the expense is still saved.

## Anomaly Rules (v1, rule-based)

1. **Category Z-score** — flags if amount exceeds mean + 2σ of category history
2. **Hard-cap** — per-category upper bounds (cold-start fallback)
3. **Rent/Loan deviation** — flags >10% deviation from last payment
4. **Daily spike** — flags if day's total is >3× the 30-day daily average
5. **Frequency** — flags 3+ expenses in the same category on one day

Each rule is a pure function, unit-tested with no DB mocking required.

## Real-Time Delivery

Polling (not WebSockets) for v1 — a deliberate trade-off. Frontend re-fetches every 8s plus an immediate re-fetch after each successful POST. Stateles, simple to debug.

## Project Structure

```
├── docker-compose.yml          # db + backend + frontend
├── .env                        # DB creds + URLs (gitignored)
├── backend/
│   ├── Dockerfile
│   ├── db/init.sql             # schema
│   ├── app/
│   │   ├── main.py             # FastAPI routes
│   │   ├── database.py         # SQLAlchemy engine/session
│   │   ├── models.py           # ORM models
│   │   ├── schemas.py          # Pydantic schemas
│   │   ├── crud.py             # DB operations
│   │   └── anomaly/
│   │       ├── rules.py        # pure rule functions
│   │       └── detector.py     # orchestrates rules + DB context
│   └── tests/test_rules.py     # 25 unit tests
└── frontend/
    ├── Dockerfile               # multi-stage: Vite build → nginx
    ├── nginx.conf
    └── src/
        ├── App.jsx
        ├── api/client.js
        ├── hooks/usePolling.js
        └── components/          # Form, Table, TrendChart, CategoryPie, AnomalyList
```

## Running

```bash
docker compose up --build       # add sudo if not in docker group
```

| URL                        | What            |
| -------------------------- | --------------- |
| http://localhost:5173      | React dashboard |
| http://localhost:8000/docs | Swagger UI      |

## Testing

```bash
cd backend
pytest tests/test_rules.py -v
```
