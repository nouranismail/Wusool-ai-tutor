"""
In-memory WebSocket connection manager.

Tracks:
  - Presence connections: child_id -> WebSocket
  - Session room connections: session_id -> {child_id -> WebSocket}

This is a single-process in-memory implementation.
For multi-instance deployments, replace with a Redis-backed pub/sub broker.
"""
from __future__ import annotations

from fastapi import WebSocket


class ConnectionManager:
    def __init__(self) -> None:
        # child_id -> WebSocket
        self.presence: dict[int, WebSocket] = {}
        # session_id -> {child_id -> WebSocket}
        self.sessions: dict[str, dict[int, WebSocket]] = {}

    # ------------------------------------------------------------------
    # Presence
    # ------------------------------------------------------------------

    async def connect_presence(self, child_id: int, ws: WebSocket) -> None:
        await ws.accept()
        self.presence[child_id] = ws

    def disconnect_presence(self, child_id: int) -> None:
        self.presence.pop(child_id, None)

    def is_online(self, child_id: int) -> bool:
        return child_id in self.presence

    async def notify_presence_change(
        self, child_id: int, online: bool, friend_ids: list[int]
    ) -> None:
        """Push an online-status change to all connected friends."""
        message = {"type": "presence", "userId": child_id, "online": online}
        for fid in friend_ids:
            ws = self.presence.get(fid)
            if ws:
                try:
                    await ws.send_json(message)
                except Exception:
                    pass

    async def send_to_child(self, child_id: int, message: dict) -> None:
        """Send a message to a specific child's presence socket."""
        ws = self.presence.get(child_id)
        if ws:
            try:
                await ws.send_json(message)
            except Exception:
                pass

    # ------------------------------------------------------------------
    # Session rooms
    # ------------------------------------------------------------------

    async def connect_session(
        self, session_id: str, child_id: int, ws: WebSocket
    ) -> None:
        await ws.accept()
        if session_id not in self.sessions:
            self.sessions[session_id] = {}
        self.sessions[session_id][child_id] = ws

    def disconnect_session(self, session_id: str, child_id: int) -> None:
        if session_id in self.sessions:
            self.sessions[session_id].pop(child_id, None)
            if not self.sessions[session_id]:
                del self.sessions[session_id]

    def session_participant_count(self, session_id: str) -> int:
        return len(self.sessions.get(session_id, {}))

    async def broadcast_to_session(
        self,
        session_id: str,
        message: dict,
        exclude_child_id: int | None = None,
    ) -> None:
        """Send a message to all participants in a session, optionally excluding one."""
        for child_id, ws in list(self.sessions.get(session_id, {}).items()):
            if child_id == exclude_child_id:
                continue
            try:
                await ws.send_json(message)
            except Exception:
                pass


# Global singleton shared across the entire application process
manager = ConnectionManager()
