"""Detector that gathers DB context and runs all rules against a single expense.

Keeps the rule *functions* pure (in ``rules.py``) while this module owns the
"glue" — fetching history, handling missing data, persisting flagged anomalies.
Importantly, any exception here is swallowed by the caller so the core
expense-write path is never affected.
"""

from __future__ import annotations

import logging
from typing import Optional

from sqlalchemy.orm import Session

from . import rules
from .. import crud

logger = logging.getLogger("anomaly.detector")


def run_anomaly_check(db: Session, expense_id: int) -> None:
    """Entry point — called via FastAPI BackgroundTasks after an expense is saved.

    Exceptions are caught and logged so the core write path is never affected.
    """
    try:
        expense = crud.get_expense(db, expense_id)
        if expense is None:
            logger.warning("Anomaly check skipped — expense %s not found", expense_id)
            return

        results = run_all_rules(
            amount=float(expense.amount),
            category=expense.category,
            expense_date=expense.expense_date,
            user_id=expense.user_id,
            db=db,
        )

        for r in results:
            crud.create_anomaly(
                db,
                expense_id=expense.id,
                reason=r.reason,
                rule_triggered=r.rule_triggered,
                severity=r.severity,
            )
            logger.info("Anomaly flagged for expense %s: %s (%s)", expense.id, r.reason, r.rule_triggered)
    except Exception as exc:  # noqa: BLE001 — intentionally broad
        logger.error("Anomaly check failed for expense %s: %s", expense_id, exc)


def run_all_rules(
    amount: float,
    category: str,
    expense_date,
    user_id: int,
    db: Session,
) -> list[rules.AnomalyResult]:
    """Gather context from the DB and run every applicable rule."""
    results: list[rules.AnomalyResult] = []

    # Rule 1 — z-score (needs prior history)
    history = crud.get_category_history(db, category, user_id)
    # The list is ordered newest-first; the just-saved expense is at index 0.
    # Exclude it from the "past" history the z-score compares against.
    prior_history = history[1:] if history else []
    z = rules.check_category_zscore(amount, prior_history)
    if z:
        results.append(z)

    # Rule 2a — hard cap
    hc = rules.check_hard_cap(amount, category)
    if hc:
        results.append(hc)

    # Rule 2b — rent deviation
    if category == "rent":
        last_rent_raw = crud.get_last_amount_for_category(db, category, user_id)
        # The "last" query returns the most-recent row — which is the one we
        # just saved.  Look at the second-newest instead.
        last_rent = None
        if len(history) >= 2:
            last_rent = history[1]
        r = rules.check_rent_deviation(amount, last_rent)
        if r:
            results.append(r)

    # Rule 2c — student loan deviation
    if category == "student_loan":
        last_loan = history[1] if len(history) >= 2 else None
        l = rules.check_loan_deviation(amount, last_loan)
        if l:
            results.append(l)

    # Rule 3 — daily spike
    today_total = crud.get_today_total(db, user_id, expense_date)
    avg_daily = crud.get_avg_daily_spend(db, user_id)
    ds = rules.check_daily_spike(today_total, avg_daily)
    if ds:
        results.append(ds)

    # Rule 4 — frequency
    count_today = crud.count_category_on_date(db, category, user_id, expense_date)
    freq = rules.check_frequency(count_today)
    if freq:
        results.append(freq)

    return results