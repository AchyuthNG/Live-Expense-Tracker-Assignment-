"""FastAPI application — Live Expense Tracker backend.

 the expense write path is the source of truth;
anomaly detection runs after-save via BackgroundTasks and never blocks or
fails the main request.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from datetime import date, timedelta

from fastapi import FastAPI, BackgroundTasks, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from . import crud, schemas
from .database import get_db, init_db
from .anomaly.detector import run_anomaly_check

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("app")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create the schema on startup (idempotent — uses IF NOT EXISTS).
    try:
        init_db()
        logger.info("Database initialised")
    except Exception as exc:  # noqa: BLE001
        logger.error("DB init failed: %s", exc)
    yield


app = FastAPI(title="Live Expense Tracker API", version="1.0.0", lifespan=lifespan)

# Allow the Vite dev-server / nginx frontend to talk to us.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------

@app.get("/api/health")
def health():
    return {"status": "ok"}


# ---------------------------------------------------------------------------
# Expenses
# ---------------------------------------------------------------------------

@app.post("/api/expenses", response_model=schemas.ExpenseOut, status_code=201)
def create_expense(
    expense: schemas.ExpenseIn,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """Create an expense.  Saves to DB FIRST, then fires anomaly detection
    as a best-effort background task — the client never waits on detection."""
    saved = crud.create_expense(
        db,
        amount=expense.amount,
        category=expense.category,
        expense_date=expense.expense_date,
        description=expense.description,
        user_id=expense.user_id,
    )
    # Fire-and-forget — detection can never block or fail this request.
    background_tasks.add_task(_safe_anomaly_check, saved.id)
    return saved


def _safe_anomaly_check(expense_id: int):
    """Wrap the detector in its own DB session + error swallowing so the
    BackgroundTask never raises into the response cycle."""
    from .database import SessionLocal
    db = SessionLocal()
    try:
        run_anomaly_check(db, expense_id)
    except Exception as exc:  # noqa: BLE001
        logger.error("Background anomaly check failed (expense %s): %s", expense_id, exc)
    finally:
        db.close()


@app.get("/api/expenses", response_model=list[schemas.ExpenseOut])
def list_expenses(
    start_date: date | None = Query(None),
    end_date: date | None = Query(None),
    category: str | None = Query(None),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    return crud.list_expenses(db, start_date=start_date, end_date=end_date,
                             category=category, limit=limit)


@app.get("/api/expenses/{expense_id}", response_model=schemas.ExpenseOut)
def get_expense(expense_id: int, db: Session = Depends(get_db)):
    expense = crud.get_expense(db, expense_id)
    if expense is None:
        raise HTTPException(status_code=404, detail="Expense not found")
    return expense


@app.delete("/api/expenses/{expense_id}", status_code=204)
def delete_expense(expense_id: int, db: Session = Depends(get_db)):
    deleted = crud.delete_expense(db, expense_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Expense not found")
    return None


# ---------------------------------------------------------------------------
# Anomalies
# ---------------------------------------------------------------------------

@app.get("/api/anomalies", response_model=list[schemas.AnomalyWithExpenseOut])
def list_anomalies(limit: int = Query(100, ge=1, le=500), db: Session = Depends(get_db)):
    return crud.list_anomalies(db, limit=limit)


# ---------------------------------------------------------------------------
# Stats
# ---------------------------------------------------------------------------

@app.get("/api/stats/trend", response_model=list[schemas.TrendPoint])
def stats_trend(days: int = Query(30, ge=1, le=365), db: Session = Depends(get_db)):
    """Daily totals for last N days plus a 7-day rolling average trend line."""
    rows = crud.daily_totals(db, user_id=1, days=days)
    totals_by_date: dict[date, float] = {row[0]: float(row[1]) for row in rows}

    today = date.today()
    dates: list[date] = [today - timedelta(days=i) for i in range(days - 1, -1, -1)]

    points: list[schemas.TrendPoint] = []
    daily_vals: list[float] = []
    for d in dates:
        daily = totals_by_date.get(d, 0.0)
        daily_vals.append(daily)
        # 7-day rolling average ending at current day
        window = daily_vals[-7:]
        trend = sum(window) / len(window)
        points.append(schemas.TrendPoint(date=d, daily=daily, trend=round(trend, 2)))
    return points


@app.get("/api/stats/by-category", response_model=list[schemas.CategoryTotal])
def stats_by_category(days: int = Query(30, ge=1, le=365), db: Session = Depends(get_db)):
    rows = crud.category_totals(db, user_id=1, days=days)
    return [schemas.CategoryTotal(category=r[0], total=round(float(r[1]), 2)) for r in rows]