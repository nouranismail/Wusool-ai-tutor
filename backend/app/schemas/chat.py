from __future__ import annotations
from typing import Optional
from pydantic import BaseModel


class ChatSource(BaseModel):
    title: str
    snippet: str


class SendMessageRequest(BaseModel):
    message: str
    lessonId: str
    lang: str = "ar"
    conversationId: Optional[str] = None


class SendMessageResponse(BaseModel):
    reply: str
    conversationId: str
    sources: Optional[list[ChatSource]] = None
