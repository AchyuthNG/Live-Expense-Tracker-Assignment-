"""CRUD operations for expenses and anomalies."""

from __future__ import annotations

from datetime import date, timedelta
from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.orm import Session

from .models import Expense, Anomaly


# ---------------------------------------------------------------------------
# Expenses
# ---------------------------------------------------------------------------

def create_expense(db: Session, amount: float, category: str, expense_date: date,
                   description: Optional[str] = None, user_id: int = 1) -> Expense:
    expense = Expense(
        amount=amount,
        category=category,
        description=description,
        expense_date=expense_date,
        user_id=user_id,
    )
    db.add(expense)
    db.commit()
    db.refresh(expense)
    return expense


def get_expense(db: Session, expense_id: int) -> Optional[Expense]:
    return db.get(Expense, expense_id)


def list_expenses(
    db: Session,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    category: Optional[str] = None,
    limit: int = 100,
) -> list[Expense]:
    stmt = select(Expense).order_by(Expense.expense_date.desc(), Expense.id.desc())
    if start_date:
        stmt = stmt.where(Expense.expense_date >= start_date)
    if end_date:
        stmt = stmt.where(Expense.expense_date <= end_date)
    if category:
        stmt = stmt.where(Expense.category == category)
    stmt = stmt.limit(limit)
    return db.scalars(stmt).all()


def delete_expense(db: Session, expense_id: int) -> bool:
    expense = db.get(Expense, expense_id)
    if expense is None:
        return False
    db.delete(expense)
    db.commit()
    return True


# ---------------------------------------------------------------------------
# Anomalies
# ---------------------------------------------------------------------------

def create_anomaly(db: Session, expense_id: int, reason: str,
                   rule_triggered: str, severity: str = "medium") -> Anomaly:
    anomaly = Anomaly(
        expense_id=expense_id,
        reason=reason,
        rule_triggered=rule_triggered,
        severity=severity,
    )
    db.add(anomaly)
    db.commit()
    db.refresh(anomaly)
    return anomaly


def list_anomalies(db: Session, limit: int = 100) -> list[Anomaly]:
    stmt = select(Anomaly).order_by(Anomaly.detected_at.desc()).limit(limit)
    return db.scalars(stmt).all()


# ---------------------------------------------------------------------------
# Stats helpers
# ---------------------------------------------------------------------------

def daily_totals(db: Session, user_id: int, days: int):
    cutoff = date.today() - timedelta(days=days - 1)
    stmt = (
        select(Expense.expense_date, func.sum(Expense.amount).label("daily"))
        .where(Expense.user_id == user_id, Expense.expense_date >= cutoff)
        .group_by(Expense.expense_date)
        .order_by(Expense.expense_date.asc())
    )
    return db.execute(stmt).all()


def category_totals(db: Session, user_id: int, days: int):
    cutoff = date.today() - timedelta(days=days - 1)
    stmt = (
        select(Expense.category, func.sum(Expense.amount).label("total"))
        .where(Expense.user_id == user_id, Expense.expense_date >= cutoff)
        .group_by(Expense.category)
    )
    return db.execute(stmt).all()


# ---------------------------------------------------------------------------
# Context helpers for the anomaly detector
# ---------------------------------------------------------------------------

def get_category_history(db: Session, category: str, user_id: int = 1) -> list[float]:
    stmt = (
        select(Expense.amount)
        .where(Expense.category == category, Expense.user_id == user_id)
        .order_by(Expense.created_at.desc())
    )
    return [float(r) for r in db.scalars(stmt).all()]


def get_last_amount_for_category(db: Session, category: str, user_id: int = 1):
    stmt = (
        select(Expense.amount)
        .where(Expense.category == category, Expense.user_id == user_id)
        .order_by(Expense.created_at.desc())
        .limit(1)
    )
    return db.scalars(stmt).first()


def get_today_total(db: Session, user_id: int, target_date: date) -> float:
    stmt = select(func.sum(Expense.amount)).where(
        Expense.user_id == user_id, Expense.expense_date == target_date
    )
    return float(db.scalars(stmt).first() or 0.0)


def get_avg_daily_spend(db: Session, user_id: int, days: int = 30) -> float:
    cutoff = date.today() - timedelta(days=days)
    stmt = select(func.sum(Expense.amount)).where(
        Expense.user_id == user_id, Expense.expense_date >= cutoff
    )
    total = float(db.scalars(stmt).first() or 0.0)
    return total / days if days > 0 else 0.0


def count_category_on_date(db: Session, category: str, user_id: int, target_date: date) -> int:
    stmt = select(func.count(Expense.id)).where(
        Expense.user_id == user_id, Expense.category == category, Expense.expense_date == target_date
    )
    return int(db.scalars(stmt).first() or 0)