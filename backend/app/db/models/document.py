from __future__ import annotations
from datetime import datetime
from sqlalchemy import Column, String, DateTime
from backend.app.db.base import Base


class RAGDocument(Base):
    __tablename__ = "rag_documents"

    id = Column(String(100), primary_key=True)
    filename = Column(String(255), nullable=False)
    lesson_id = Column(String(100), nullable=True)
    status = Column(String(50), nullable=False, default="indexed")
    uploaded_at = Column(DateTime, default=datetime.utcnow, nullable=False)
