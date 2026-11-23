"""
GET  /api/sessions
POST /api/sessions/{id}/join
POST /api/sessions/private
POST /api/sessions/{id}/invitations
POST /api/sessions/{id}/leave
POST /api/sessions/{id}/voice
"""
from __future__ import annotations
import asyncio
import time

from fastapi import APIRouter, Depends, File, HTTPException, Response, UploadFile
from sqlalchemy.orm import Session

from backend.app.core.dependencies import get_current_child, get_db
from backend.app.core.websocket_manager import manager as ws_manager
from backend.app.db.models.child import Child
from backend.app.db.models.english_session import EnglishSession, SessionParticipant
from backend.app.db.models.friend import Friendship
from backend.app.schemas.session import (
    CreatePrivateSessionRequest,
    CreatePrivateSessionResponse,
    InviteFriendRequest,
    InviteFriendResponse,
    JoinSessionResponse,
    ParticipantOut,
    SessionOut,
)

router = APIRouter()
MAX_HUMAN = 2

_DEFAULT_SESSIONS = [
    {"id": "space",      "title": "Space Adventure",  "title_ar": "مغامرة في الفضاء",   "level": "beginner"},
    {"id": "animals-en", "title": "Animal Kingdom",   "title_ar": "مملكة الحيوانات",    "level": "intermediate"},
]


def _are_friends(db: Session, a: int, b: int) -> bool:
    return db.query(Friendship).filter(
        ((Friendship.child_a_id == a) & (Friendship.child_b_id == b)) |
        ((Friendship.child_a_id == b) & (Friendship.child_b_id == a))
    ).first() is not None


def _participant_count(db: Session, session_id: str) -> int:
    return db.query(SessionParticipant).filter(
        SessionParticipant.session_id == session_id
    ).count()


def _seed_default_sessions(db: Session) -> None:
    for s in _DEFAULT_SESSIONS:
        if not db.query(EnglishSession).filter(EnglishSession.id == s["id"]).first():
            db.add(EnglishSession(
                id=s["id"], title=s["title"],
                title_ar=s["title_ar"], level=s["level"],
            ))
    db.commit()


@router.get("/sessions", response_model=list[SessionOut])
def list_sessions(
    child: Child = Depends(get_current_child),
    db: Session = Depends(get_db),
):
    _seed_default_sessions(db)
    db_sessions = db.query(EnglishSession).filter(EnglishSession.is_private.is_(False)).all()
    result = []
    for s in db_sessions:
        parts = db.query(SessionParticipant).filter(
            SessionParticipant.session_id == s.id
        ).all()
        children = db.query(Child).filter(Child.id.in_([p.child_id for p in parts])).all()
        result.append(SessionOut(
            id=s.id, title=s.title, titleAr=s.title_ar,
            level=s.level, people=len(parts), max=MAX_HUMAN, time="5:00",
            participants=[ParticipantOut(name=c.name) for c in children],
        ))
    return result


@router.post("/sessions/{session_id}/join", response_model=JoinSessionResponse)
def join_session(
    session_id: str,
    child: Child = Depends(get_current_child),
    db: Session = Depends(get_db),
):
    session = db.query(EnglishSession).filter(EnglishSession.id == session_id).first()
    if not session:
        raise HTTPException(404, "Session not found")

    already = db.query(SessionParticipant).filter(
        SessionParticipant.session_id == session_id,
        SessionParticipant.child_id == child.id,
    ).first()
    if not already:
        if _participant_count(db, session_id) >= MAX_HUMAN:
            raise HTTPException(400, "Session is full")
        db.add(SessionParticipant(session_id=session_id, child_id=child.id))
        db.commit()

    return JoinSessionResponse(roomId=session_id, wsToken=None)


@router.post("/sessions/private", response_model=CreatePrivateSessionResponse, status_code=201)
def create_private_session(
    body: CreatePrivateSessionRequest,
    child: Child = Depends(get_current_child),
    db: Session = Depends(get_db),
):
    invitee = db.query(Child).filter(Child.username == body.username).first()
    if not invitee:
        raise HTTPException(404, "User not found")
    if not _are_friends(db, child.id, invitee.id):
        raise HTTPException(403, "You can only invite friends to a private session")

    session_id = f"private-{int(time.time() * 1000)}"
    session = EnglishSession(
        id=session_id, title=body.title, title_ar=body.title,
        level="beginner", is_private=True,
    )
    db.add(session)
    db.add(SessionParticipant(session_id=session_id, child_id=child.id))
    db.commit()

    # Notify invitee via their presence WebSocket
    invitation_msg = {
        "type": "invitation",
        "sessionId": session_id,
        "sessionTitle": body.title,
        "from": {"name": child.name, "username": child.username},
    }
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            loop.create_task(ws_manager.send_to_child(invitee.id, invitation_msg))
    except Exception:
        pass

    return CreatePrivateSessionResponse(id=session_id, title=body.title)


@router.post("/sessions/{session_id}/invitations", response_model=InviteFriendResponse)
def invite_to_session(
    session_id: str,
    body: InviteFriendRequest,
    child: Child = Depends(get_current_child),
    db: Session = Depends(get_db),
):
    session = db.query(EnglishSession).filter(EnglishSession.id == session_id).first()
    if not session:
        raise HTTPException(404, "Session not found")
    if _participant_count(db, session_id) >= MAX_HUMAN:
        raise HTTPException(400, "Session is full")
    if not _are_friends(db, child.id, body.friendId):
        raise HTTPException(403, "You can only invite friends")
    if not ws_manager.is_online(body.friendId):
        raise HTTPException(400, "Friend is not online")

    friend = db.query(Child).filter(Child.id == body.friendId).first()
    if not friend:
        raise HTTPException(404, "Friend not found")

    msg = {
        "type": "invitation",
        "sessionId": session_id,
        "sessionTitle": session.title,
        "from": {"name": child.name, "username": child.username},
    }
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            loop.create_task(ws_manager.send_to_child(body.friendId, msg))
    except Exception:
        pass

    return InviteFriendResponse(ok=True)


@router.post("/sessions/{session_id}/leave", status_code=204)
def leave_session(
    session_id: str,
    child: Child = Depends(get_current_child),
    db: Session = Depends(get_db),
):
    part = db.query(SessionParticipant).filter(
        SessionParticipant.session_id == session_id,
        SessionParticipant.child_id == child.id,
    ).first()
    if part:
        db.delete(part)
        db.commit()
    return Response(status_code=204)


@router.post("/sessions/{session_id}/voice", status_code=204)
async def session_voice(
    session_id: str,
    audio: UploadFile = File(...),
    child: Child = Depends(get_current_child),
):
    """
    Voice message inside a session room.
    AI response arrives asynchronously via the session WebSocket.
    Mock: simply acknowledges receipt.
    """
    return Response(status_code=204)
