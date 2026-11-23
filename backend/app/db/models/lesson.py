from __future__ import annotations
from sqlalchemy import Column, String, Integer, Text, ForeignKey
from backend.app.db.base import Base


class Lesson(Base):
    __tablename__ = "lessons"

    id = Column(String(100), primary_key=True)       # slug e.g. "animals", "ict-3"
    title = Column(String(255), nullable=False)
    subject = Column(String(50), nullable=False)      # "english" | "ict"
    grade = Column(Integer, nullable=False)


class Question(Base):
    """Globally unique question across the entire application."""
    __tablename__ = "questions"

    id = Column(String(50), primary_key=True)        # e.g. "q_000001"
    lesson_id = Column(
        String(100),
        ForeignKey("lessons.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    text = Column(Text, nullable=False)
    correct_option_id = Column(String(10), nullable=False)  # NEVER sent to client


class QuestionOption(Base):
    __tablename__ = "question_options"

    id = Column(String(10), primary_key=True)
    question_id = Column(
        String(50),
        ForeignKey("questions.id", ondelete="CASCADE"),
        primary_key=True,
    )
    label = Column(Text, nullable=False)
