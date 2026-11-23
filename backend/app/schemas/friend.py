from __future__ import annotations
from typing import Optional
from pydantic import BaseModel


class FriendOut(BaseModel):
    id: int
    name: str
    username: str
    online: bool


class FriendRef(BaseModel):
    name: str
    username: str


class FriendRequestOut(BaseModel):
    id: int
    to: Optional[FriendRef] = None
    from_field: Optional[FriendRef] = None
    status: str

    model_config = {"populate_by_name": True}


class FriendRequestsResponse(BaseModel):
    sent: list[FriendRequestOut]
    received: list[FriendRequestOut]


class ParentApprovalItem(BaseModel):
    id: int
    stage: str
    child: dict
    otherChild: dict


class SendFriendRequestBody(BaseModel):
    username: str


class SendFriendRequestResponse(BaseModel):
    id: int
    status: str


class ParentPasswordBody(BaseModel):
    parentPassword: str


class ApproveRejectResponse(BaseModel):
    ok: bool
    status: str
