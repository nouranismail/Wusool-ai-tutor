from __future__ import annotations
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from backend.app.db.base import Base


class Child(Base):
    __tablename__ = "children"

    id = Column(Integer, primary_key=True, index=True)
    parent_id = Column(
        Integer,
        ForeignKey("parents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name = Column(String(255), nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=False)
    grade = Column(Integer, nullable=False)
    lang = Column(String(10), nullable=False, default="ar")

    # Accessibility stored as three independent booleans.
    # The old accessibilityNeed string field does not exist in the database.
    dyslexia_font = Column(Boolean, nullable=False, default=False)
    high_contrast = Column(Boolean, nullable=False, default=False)
    read_aloud = Column(Boolean, nullable=False, default=False)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
