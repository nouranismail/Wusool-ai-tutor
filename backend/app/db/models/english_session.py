from __future__ import annotations
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from backend.app.db.base import Base


class EnglishSession(Base):
    __tablename__ = "english_sessions"

    id = Column(String(100), primary_key=True)
    title = Column(String(255), nullable=False)
    title_ar = Column(String(255), nullable=False, default="")
    level = Column(String(50), nullable=False, default="beginner")
    is_private = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class SessionParticipant(Base):
    __tablename__ = "session_participants"

    id = Column(Integer, primary_key=True)
    session_id = Column(
        String(100),
        ForeignKey("english_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    child_id = Column(
        Integer,
        ForeignKey("children.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    joined_at = Column(DateTime, default=datetime.utcnow, nullable=False)
