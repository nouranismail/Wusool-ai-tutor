from __future__ import annotations
from typing import Optional
from pydantic import BaseModel


class STTResponse(BaseModel):
    text: str


class VoiceChatResponse(BaseModel):
    transcript: str
    reply: str
    audioUrl: Optional[str] = None


class RAGDocumentResponse(BaseModel):
    id: str
    status: str
