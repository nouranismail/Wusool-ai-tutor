from __future__ import annotations
from typing import Optional
from pydantic import BaseModel


class ParticipantOut(BaseModel):
    name: str


class SessionOut(BaseModel):
    id: str
    title: str
    titleAr: str
    level: str
    people: int
    max: int = 2
    time: str
    participants: list[ParticipantOut]


class JoinSessionResponse(BaseModel):
    roomId: str
    wsToken: Optional[str] = None


class CreatePrivateSessionRequest(BaseModel):
    title: str
    username: str


class CreatePrivateSessionResponse(BaseModel):
    id: str
    title: str


class InviteFriendRequest(BaseModel):
    friendId: int


class InviteFriendResponse(BaseModel):
    ok: bool
