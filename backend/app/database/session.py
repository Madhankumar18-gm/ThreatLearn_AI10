"""
Database session management using SQLAlchemy and SQLite.
Enforces local file persistence that survives backend restarts (Feature F51).
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from backend.app.core.config import settings

engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False},  # Required for SQLite in FastAPI
    echo=False
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    from backend.app.database import models
    from sqlalchemy import text
    Base.metadata.create_all(bind=engine)
    with engine.begin() as conn:
        try:
            conn.execute(text("ALTER TABLE scenarios ADD COLUMN is_custom BOOLEAN DEFAULT 0"))
        except Exception:
            pass
        try:
            conn.execute(text("ALTER TABLE scenarios ADD COLUMN is_held_out BOOLEAN DEFAULT 0"))
        except Exception:
            pass
