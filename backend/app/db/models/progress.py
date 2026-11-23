from __future__ import annotations
from datetime import datetime
from sqlalchemy import Column, Integer, Float, String, DateTime, ForeignKey
from backend.app.db.base import Base


class Progress(Base):
    __tablename__ = "progress"

    id = Column(Integer, primary_key=True)
    child_id = Column(
        Integer,
        ForeignKey("children.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )
    lessons_count = Column(Integer, nullable=False, default=0)
    exercises_count = Column(Integer, nullable=False, default=0)
    hours = Column(Float, nullable=False, default=0.0)
    streak = Column(Integer, nullable=False, default=0)


class Activity(Base):
    __tablename__ = "activities"

    id = Column(Integer, primary_key=True)
    child_id = Column(
        Integer,
        ForeignKey("children.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    activity_id = Column(String(255), nullable=False)
    recorded_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class Badge(Base):
    __tablename__ = "badges"

    id = Column(Integer, primary_key=True)
    child_id = Column(
        Integer,
        ForeignKey("children.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    badge_key = Column(String(100), nullable=False)
