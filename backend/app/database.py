"""Database connection and session management for the Live Expense Tracker backend."""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg://expense_user:expense_pass@localhost:5432/expensedb")

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()


def get_db():
    """FastAPI dependency that yields a DB session and closes it after the request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Create all tables if they don't yet exist. Uses raw SQL from init.sql for schema."""
    from sqlalchemy import text

    init_path = os.path.join(os.path.dirname(__file__), "..", "db", "init.sql")
    init_path = os.path.abspath(init_path)
    with open(init_path, "r") as f:
        sql = f.read()
    with engine.connect() as conn:
        for statement in sql.split(";"):
            stmt = statement.strip()
            if stmt:
                conn.execute(text(stmt))
        conn.commit()