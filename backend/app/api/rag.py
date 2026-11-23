"""POST /api/rag/documents  — Admin only"""
from __future__ import annotations
import uuid

from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy.orm import Session

from backend.app.core.dependencies import get_admin, get_db
from backend.app.db.models.document import RAGDocument
from backend.app.schemas.voice import RAGDocumentResponse

router = APIRouter()


@router.post("/rag/documents", response_model=RAGDocumentResponse, status_code=201)
async def upload_document(
    file: UploadFile = File(...),
    lessonId: str = Form(default=""),
    _admin: bool = Depends(get_admin),
    db: Session = Depends(get_db),
):
    doc_id = f"doc-{str(uuid.uuid4())[:8]}"
    doc = RAGDocument(
        id=doc_id,
        filename=file.filename or "unknown",
        lesson_id=lessonId or None,
        status="indexed",
    )
    db.add(doc)
    db.commit()
    return RAGDocumentResponse(id=doc_id, status="indexed")
