"""
SQLAlchemy engine and session factory.

The connection string is read from DATABASE_URL in .env.
Never hardcode connection details here.
"""
from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app.core.config import settings

engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,  # automatically reconnect on stale connections
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
