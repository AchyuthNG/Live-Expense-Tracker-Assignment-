"""SQLAlchemy ORM models — mirrors the schema in db/init.sql."""

from sqlalchemy import Column, Integer, Numeric, String, Date, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship

from .database import Base


class Expense(Base):
    __tablename__ = "expenses"

    id = Column(Integer, primary_key=True, index=True)
    amount = Column(Numeric(10, 2), nullable=False)
    category = Column(String(50), nullable=False)
    description = Column(String(255), nullable=True)
    expense_date = Column(Date, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    user_id = Column(Integer, nullable=False, default=1)

    anomaly = relationship("Anomaly", back_populates="expense", cascade="all, delete-orphan", uselist=False)


class Anomaly(Base):
    __tablename__ = "anomalies"

    id = Column(Integer, primary_key=True, index=True)
    expense_id = Column(Integer, ForeignKey("expenses.id", ondelete="CASCADE"), nullable=False)
    reason = Column(String(255), nullable=False)
    rule_triggered = Column(String(100), nullable=False)
    severity = Column(String(20), nullable=False, default="medium")
    detected_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    expense = relationship("Expense", back_populates="anomaly")