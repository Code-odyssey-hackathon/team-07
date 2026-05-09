"""
Madhyastha — Database Setup
SQLAlchemy engine, session factory, and base class
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

# Handle SQLite-specific connection args
connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    echo=settings.DEBUG,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def init_db():
    """Create all tables in the database"""
    from app.models.models import (
        Dispute, Party, Statement, MediationSession,
        Agreement, ArbitrationCase, Arbitrator
    )
    Base.metadata.create_all(bind=engine)


def get_db_session():
    """Get a database session (for scripts)"""
    db = SessionLocal()
    try:
        return db
    except Exception:
        db.close()
        raise
