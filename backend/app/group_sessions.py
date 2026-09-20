from __future__ import annotations

import secrets
from dataclasses import dataclass, field

from fastapi import WebSocket


@dataclass
class GroupRoom:
    code: str
    lesson: dict
    host_token: str
    participants: list[str] = field(default_factory=list)
    sockets: dict[str, WebSocket] = field(default_factory=dict)
    current_turn: int = 0
    question_index: int = 0
    active: bool = False

    def public_state(self) -> dict:
        current = self.participants[self.current_turn] if self.active and self.participants else None
        return {"type": "room_state", "code": self.code, "lesson_title": self.lesson["title_ar"], "participants": self.participants, "current_participant": current, "question_index": self.question_index, "question_count": len(self.lesson["questions"]), "active": self.active}


class GroupSessionManager:
    def __init__(self, lessons: list[dict]) -> None:
        self.lessons = {lesson["id"]: lesson for lesson in lessons}
        self.rooms: dict[str, GroupRoom] = {}

    def create(self, lesson_id: str) -> GroupRoom:
        lesson = self.lessons.get(lesson_id)
        if lesson is None:
            raise KeyError("Lesson not found")
        code = "".join(secrets.choice("ABCDEFGHJKLMNPQRSTUVWXYZ23456789") for _ in range(6))
        room = GroupRoom(code=code, lesson=lesson, host_token=secrets.token_urlsafe(18))
        self.rooms[code] = room
        return room

    def get(self, code: str) -> GroupRoom | None:
        return self.rooms.get(code.upper())

    async def connect(self, room: GroupRoom, name: str, socket: WebSocket, role: str) -> None:
        await socket.accept()
        room.sockets[f"{role}:{name}"] = socket
        if role == "participant" and name not in room.participants:
            room.participants.append(name)
        await self.broadcast(room, room.public_state())

    async def disconnect(self, room: GroupRoom, name: str, role: str) -> None:
        room.sockets.pop(f"{role}:{name}", None)
        if role == "participant" and name in room.participants:
            room.participants.remove(name)
            room.current_turn %= max(1, len(room.participants))
            if not room.participants:
                room.active = False
        await self.broadcast(room, room.public_state())

    async def broadcast(self, room: GroupRoom, payload: dict) -> None:
        stale = []
        for key, socket in room.sockets.items():
            try:
                await socket.send_json(payload)
            except RuntimeError:
                stale.append(key)
        for key in stale:
            room.sockets.pop(key, None)

    async def start(self, room: GroupRoom) -> None:
        if not room.participants:
            await self.broadcast(room, {"type": "error", "message": "أضيفوا طفلًا واحدًا على الأقل قبل البدء."})
            return
        room.active, room.current_turn, room.question_index = True, 0, 0
        await self.broadcast(room, room.public_state())
        await self.ask_current(room)

    async def ask_current(self, room: GroupRoom) -> None:
        question = room.lesson["questions"][room.question_index]
        await self.broadcast(room, {"type": "question", "participant": room.participants[room.current_turn], "question_id": question["id"], "text": question["question_ar"]})

    async def submit_answer(self, room: GroupRoom, name: str, answer: str, normalize) -> None:
        if not room.active or not room.participants or room.participants[room.current_turn] != name:
            await self.broadcast(room, {"type": "error", "message": "انتظر دورك من فضلك."})
            return
        question = room.lesson["questions"][room.question_index]
        correct = any(normalize(answer) == normalize(item) for item in question["accepted_answers"])
        await self.broadcast(room, {"type": "feedback", "participant": name, "correct": correct, "message": "إجابة رائعة! أحسنت." if correct else question["hint_ar"]})
        room.current_turn += 1
        if room.current_turn >= len(room.participants):
            room.current_turn, room.question_index = 0, room.question_index + 1
        if room.question_index >= len(room.lesson["questions"]):
            room.active = False
            await self.broadcast(room, {"type": "complete", "message": "انتهت الجلسة. أحسنتم جميعًا!"})
            await self.broadcast(room, room.public_state())
            return
        await self.broadcast(room, room.public_state())
        await self.ask_current(room)

