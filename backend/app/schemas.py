"""Pydantic request/response schemas."""

from datetime import date, datetime
from typing import Optional, Literal

from pydantic import BaseModel, Field, field_validator


Category = Literal[
    "groceries", "travel", "rent", "student_loan",
    "shopping", "food", "misc",
]

Severity = Literal["low", "medium", "high"]


class ExpenseIn(BaseModel):
    amount: float = Field(..., gt=0)
    category: Category
    description: Optional[str] = None
    expense_date: date
    user_id: int = Field(1, ge=1)

    @field_validator("description")
    @classmethod
    def truncate_description(cls, v):
        if v is not None:
            return v[:255]
        return v


class ExpenseOut(BaseModel):
    id: int
    amount: float
    category: str
    description: Optional[str] = None
    expense_date: date
    created_at: Optional[datetime] = None
    user_id: int
    anomaly: Optional["AnomalyOut"] = None

    model_config = {"from_attributes": True}


class AnomalyOut(BaseModel):
    id: int
    expense_id: int
    reason: str
    rule_triggered: str
    severity: Severity
    detected_at: datetime

    model_config = {"from_attributes": True}


class AnomalyWithExpenseOut(AnomalyOut):
    expense: Optional["ExpenseOut"] = None


class TrendPoint(BaseModel):
    date: date
    daily: float
    trend: float


class CategoryTotal(BaseModel):
    category: str
    total: float