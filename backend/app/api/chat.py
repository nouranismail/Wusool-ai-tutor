"""
POST /api/chat/messages
GET  /api/chat/history?conversationId=<id>
"""
from __future__ import annotations
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.app.core.dependencies import get_current_child, get_db
from backend.app.db.models.child import Child
from backend.app.db.models.conversation import Conversation, Message
from backend.app.schemas.chat import SendMessageRequest, SendMessageResponse
from backend.app.services.mock_data import mock_chat_reply

router = APIRouter()


@router.post("/chat/messages", response_model=SendMessageResponse)
def send_message(
    body: SendMessageRequest,
    child: Child = Depends(get_current_child),
    db: Session = Depends(get_db),
):
    if body.conversationId:
        conv = db.query(Conversation).filter(
            Conversation.id == body.conversationId,
            Conversation.child_id == child.id,
        ).first()
        if not conv:
            raise HTTPException(404, "Conversation not found")
        conv_id = conv.id
    else:
        conv_id = str(uuid.uuid4())[:12]
        conv = Conversation(id=conv_id, child_id=child.id, lesson_id=body.lessonId)
        db.add(conv)
        db.flush()

    db.add(Message(conversation_id=conv_id, from_role="user", text=body.message))

    result = mock_chat_reply(body.message, body.lessonId, conv_id, body.lang)

    db.add(Message(conversation_id=conv_id, from_role="ai", text=result.reply))
    db.commit()

    return result


@router.get("/chat/history")
def get_chat_history(
    conversationId: str = Query(...),
    child: Child = Depends(get_current_child),
    db: Session = Depends(get_db),
):
    conv = db.query(Conversation).filter(
        Conversation.id == conversationId,
        Conversation.child_id == child.id,
    ).first()
    if not conv:
        raise HTTPException(404, "Conversation not found")

    messages = (
        db.query(Message)
        .filter(Message.conversation_id == conversationId)
        .order_by(Message.id)
        .all()
    )
    return [{"from": m.from_role, "text": m.text} for m in messages]
