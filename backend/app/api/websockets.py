"""
WebSocket endpoints.

WS /ws/presence?token=<child_jwt>
    Persistent connection for live friend presence and social notifications.

WS /ws/sessions/{id}?token=<child_jwt>
    Live session room for English practice.
"""
from __future__ import annotations

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

from backend.app.core.dependencies import decode_ws_token
from backend.app.core.websocket_manager import manager
from backend.app.db.models.english_session import SessionParticipant
from backend.app.db.models.friend import Friendship
from backend.app.db.session import SessionLocal
from backend.app.services.mock_data import mock_ai_session_message

router = APIRouter()
MAX_HUMAN = 2


def _friend_ids(db: Session, child_id: int) -> list[int]:
    rows = db.query(Friendship).filter(
        (Friendship.child_a_id == child_id) | (Friendship.child_b_id == child_id)
    ).all()
    return [
        r.child_b_id if r.child_a_id == child_id else r.child_a_id
        for r in rows
    ]


# ---------------------------------------------------------------------------
# WS /ws/presence
# ---------------------------------------------------------------------------

@router.websocket("/presence")
async def ws_presence(ws: WebSocket, token: str = Query(...)):
    """
    Persistent connection for live friend status and social/session notifications.

    Server → client event types:
      {type: "presence",      userId: int,    online: bool}
      {type: "invitation",    sessionId: str, sessionTitle: str, from: {name, username}}
      {type: "friend_request",from: {name, username}}
    """
    db = SessionLocal()
    try:
        child = decode_ws_token(token, db)
    except Exception:
        await ws.close(code=4001)
        db.close()
        return

    child_id = child.id
    friend_ids = _friend_ids(db, child_id)
    db.close()

    await manager.connect_presence(child_id, ws)

    # Notify friends: this child came online
    await manager.notify_presence_change(child_id, online=True, friend_ids=friend_ids)

    try:
        while True:
            # Keep the connection alive; ignore client pings
            await ws.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        manager.disconnect_presence(child_id)
        # Notify friends: this child went offline
        db2 = SessionLocal()
        offline_friend_ids = _friend_ids(db2, child_id)
        db2.close()
        await manager.notify_presence_change(child_id, online=False, friend_ids=offline_friend_ids)


# ---------------------------------------------------------------------------
# WS /ws/sessions/{session_id}
# ---------------------------------------------------------------------------

@router.websocket("/sessions/{session_id}")
async def ws_session(session_id: str, ws: WebSocket, token: str = Query(...)):
    """
    Live English session room.

    Server → client event types:
      {type: "participants", list: [{id, name, username, isAI}]}
      {type: "joined",       user: {id, name}}
      {type: "left",         user: {id, name}}
      {type: "message",      from: {id, name, isAI}, text, audioUrl}
      {type: "ai_typing",    value: bool}

    Client → server event types:
      {type: "message", text: str}
      {type: "voice",   audio: "<base64>"}

    Rules enforced:
      - Max two human Children per room (product rule 9).
      - Sender's own message is NOT echoed back (product rule 15).
      - AI Tutor responds in English only (product rule 14).
    """
    db = SessionLocal()
    try:
        child = decode_ws_token(token, db)
    except Exception:
        await ws.close(code=4001)
        db.close()
        return

    # Enforce participant limit
    existing_ids = [
        p.child_id
        for p in db.query(SessionParticipant).filter(
            SessionParticipant.session_id == session_id
        ).all()
    ]
    if child.id not in existing_ids and len(existing_ids) >= MAX_HUMAN:
        await ws.close(code=4003)
        db.close()
        return

    child_id = child.id
    child_name = child.name
    db.close()

    await manager.connect_session(session_id, child_id, ws)

    # Send current participant list to the new joiner
    current_ids = list(manager.sessions.get(session_id, {}).keys())
    await ws.send_json({
        "type": "participants",
        "list": [{"id": cid, "name": f"Child {cid}", "isAI": False} for cid in current_ids],
    })

    # Notify other participants that this child joined
    await manager.broadcast_to_session(
        session_id,
        {"type": "joined", "user": {"id": child_id, "name": child_name}},
        exclude_child_id=child_id,
    )

    try:
        while True:
            data = await ws.receive_json()
            msg_type = data.get("type")

            if msg_type == "message":
                text = data.get("text", "")

                # Broadcast to other humans — do NOT echo back to sender (rule 15)
                await manager.broadcast_to_session(
                    session_id,
                    {
                        "type": "message",
                        "from": {"id": child_id, "name": child_name, "isAI": False},
                        "text": text,
                        "audioUrl": None,
                    },
                    exclude_child_id=child_id,
                )

                # AI Tutor responds in English (rule 14)
                await manager.broadcast_to_session(
                    session_id, {"type": "ai_typing", "value": True}
                )
                ai_reply = mock_ai_session_message(text)
                await manager.broadcast_to_session(
                    session_id,
                    {
                        "type": "message",
                        "from": {"id": 0, "name": "Wusool AI", "isAI": True},
                        "text": ai_reply,
                        "audioUrl": None,
                    },
                )
                await manager.broadcast_to_session(
                    session_id, {"type": "ai_typing", "value": False}
                )

            elif msg_type == "voice":
                # Mock: treat voice input as a text message placeholder
                await manager.broadcast_to_session(
                    session_id, {"type": "ai_typing", "value": True}
                )
                ai_reply = mock_ai_session_message("(voice message)")
                await manager.broadcast_to_session(
                    session_id,
                    {
                        "type": "message",
                        "from": {"id": 0, "name": "Wusool AI", "isAI": True},
                        "text": ai_reply,
                        "audioUrl": None,
                    },
                )
                await manager.broadcast_to_session(
                    session_id, {"type": "ai_typing", "value": False}
                )

    except WebSocketDisconnect:
        pass
    finally:
        manager.disconnect_session(session_id, child_id)
        await manager.broadcast_to_session(
            session_id,
            {"type": "left", "user": {"id": child_id, "name": child_name}},
        )
