"""
GET    /api/friends
GET    /api/friends/requests
POST   /api/friends/requests
GET    /api/friends/requests/parent-approval
POST   /api/friends/requests/{requestId}/parent-approve
POST   /api/friends/requests/{requestId}/parent-reject
DELETE /api/friends/requests/{requestId}
DELETE /api/friends/{friendId}
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from backend.app.core.dependencies import get_current_child, get_current_child_with_parent, get_db
from backend.app.core.security import verify_password
from backend.app.core.websocket_manager import manager as ws_manager
from backend.app.db.models.child import Child
from backend.app.db.models.friend import FriendRequest, Friendship
from backend.app.schemas.friend import (
    ApproveRejectResponse,
    FriendOut,
    FriendRef,
    FriendRequestOut,
    FriendRequestsResponse,
    ParentApprovalItem,
    ParentPasswordBody,
    SendFriendRequestBody,
    SendFriendRequestResponse,
)

router = APIRouter()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _friend_ids(db: Session, child_id: int) -> list[int]:
    rows = db.query(Friendship).filter(
        (Friendship.child_a_id == child_id) | (Friendship.child_b_id == child_id)
    ).all()
    return [
        r.child_b_id if r.child_a_id == child_id else r.child_a_id
        for r in rows
    ]


def _are_friends(db: Session, a: int, b: int) -> bool:
    return db.query(Friendship).filter(
        ((Friendship.child_a_id == a) & (Friendship.child_b_id == b)) |
        ((Friendship.child_a_id == b) & (Friendship.child_b_id == a))
    ).first() is not None


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.get("/friends", response_model=list[FriendOut])
def get_friends(
    child: Child = Depends(get_current_child),
    db: Session = Depends(get_db),
):
    ids = _friend_ids(db, child.id)
    friends = db.query(Child).filter(Child.id.in_(ids)).all()
    return [
        FriendOut(
            id=f.id,
            name=f.name,
            username=f.username,
            online=ws_manager.is_online(f.id),
        )
        for f in friends
    ]


@router.get("/friends/requests", response_model=FriendRequestsResponse)
def get_friend_requests(
    child: Child = Depends(get_current_child),
    db: Session = Depends(get_db),
):
    sent_rows = db.query(FriendRequest).filter(FriendRequest.sender_id == child.id).all()
    received_rows = db.query(FriendRequest).filter(
        FriendRequest.recipient_id == child.id,
        FriendRequest.status == "pending_recipient_parent",
    ).all()

    sent = []
    for r in sent_rows:
        recip = db.query(Child).filter(Child.id == r.recipient_id).first()
        sent.append(FriendRequestOut(
            id=r.id,
            to=FriendRef(name=recip.name, username=recip.username) if recip else None,
            status=r.status,
        ))

    received = []
    for r in received_rows:
        sender = db.query(Child).filter(Child.id == r.sender_id).first()
        received.append(FriendRequestOut(
            id=r.id,
            from_field=FriendRef(name=sender.name, username=sender.username) if sender else None,
            status=r.status,
        ))

    return FriendRequestsResponse(sent=sent, received=received)


@router.post("/friends/requests", response_model=SendFriendRequestResponse, status_code=201)
def send_friend_request(
    body: SendFriendRequestBody,
    child: Child = Depends(get_current_child),
    db: Session = Depends(get_db),
):
    target = db.query(Child).filter(Child.username == body.username).first()
    if not target:
        raise HTTPException(404, "User not found")
    if target.id == child.id:
        raise HTTPException(400, "Cannot send a friend request to yourself")
    if _are_friends(db, child.id, target.id):
        raise HTTPException(409, "Already friends")

    existing = db.query(FriendRequest).filter(
        FriendRequest.sender_id == child.id,
        FriendRequest.recipient_id == target.id,
        FriendRequest.status.in_(["pending_sender_parent", "pending_recipient_parent"]),
    ).first()
    if existing:
        raise HTTPException(409, "Friend request already pending")

    req = FriendRequest(sender_id=child.id, recipient_id=target.id)
    db.add(req)
    db.commit()
    db.refresh(req)
    return SendFriendRequestResponse(id=req.id, status=req.status)


@router.get("/friends/requests/parent-approval", response_model=list[ParentApprovalItem])
def parent_approval_list(
    child: Child = Depends(get_current_child),
    db: Session = Depends(get_db),
):
    rows = db.query(FriendRequest).filter(
        ((FriendRequest.sender_id == child.id) & (FriendRequest.status == "pending_sender_parent")) |
        ((FriendRequest.recipient_id == child.id) & (FriendRequest.status == "pending_recipient_parent"))
    ).all()

    result = []
    for r in rows:
        if r.sender_id == child.id:
            other = db.query(Child).filter(Child.id == r.recipient_id).first()
            stage = "sender_parent_approval"
        else:
            other = db.query(Child).filter(Child.id == r.sender_id).first()
            stage = "recipient_parent_approval"

        result.append(ParentApprovalItem(
            id=r.id,
            stage=stage,
            child={"id": child.id, "name": child.name, "username": child.username},
            otherChild=(
                {"id": other.id, "name": other.name, "username": other.username}
                if other else {}
            ),
        ))
    return result


@router.post("/friends/requests/{request_id}/parent-approve", response_model=ApproveRejectResponse)
def parent_approve(
    request_id: int,
    body: ParentPasswordBody,
    child_and_parent: tuple = Depends(get_current_child_with_parent),
    db: Session = Depends(get_db),
):
    child, parent = child_and_parent
    if not verify_password(body.parentPassword, parent.hashed_password):
        raise HTTPException(401, "Incorrect parent password")

    req = db.query(FriendRequest).filter(FriendRequest.id == request_id).first()
    if not req:
        raise HTTPException(404, "Request not found")

    if req.status == "pending_sender_parent" and req.sender_id == child.id:
        req.status = "pending_recipient_parent"
        db.commit()
        return ApproveRejectResponse(ok=True, status="pending_recipient_parent")
    elif req.status == "pending_recipient_parent" and req.recipient_id == child.id:
        req.status = "accepted"
        db.add(Friendship(child_a_id=req.sender_id, child_b_id=req.recipient_id))
        db.commit()
        return ApproveRejectResponse(ok=True, status="accepted")
    else:
        raise HTTPException(400, "This request is not awaiting your parent's approval")


@router.post("/friends/requests/{request_id}/parent-reject", response_model=ApproveRejectResponse)
def parent_reject(
    request_id: int,
    body: ParentPasswordBody,
    child_and_parent: tuple = Depends(get_current_child_with_parent),
    db: Session = Depends(get_db),
):
    child, parent = child_and_parent
    if not verify_password(body.parentPassword, parent.hashed_password):
        raise HTTPException(401, "Incorrect parent password")

    req = db.query(FriendRequest).filter(FriendRequest.id == request_id).first()
    if not req:
        raise HTTPException(404, "Request not found")

    if (req.status == "pending_sender_parent" and req.sender_id == child.id) or \
       (req.status == "pending_recipient_parent" and req.recipient_id == child.id):
        req.status = "rejected"
        db.commit()
        return ApproveRejectResponse(ok=True, status="rejected")
    raise HTTPException(400, "Cannot reject this request at this stage")


@router.delete("/friends/requests/{request_id}", status_code=204)
def cancel_friend_request(
    request_id: int,
    child: Child = Depends(get_current_child),
    db: Session = Depends(get_db),
):
    req = db.query(FriendRequest).filter(
        FriendRequest.id == request_id,
        FriendRequest.sender_id == child.id,
    ).first()
    if not req:
        raise HTTPException(404, "Request not found")
    if req.status == "accepted":
        raise HTTPException(400, "Cannot cancel an accepted request; use remove-friend instead")
    req.status = "cancelled"
    db.commit()
    return Response(status_code=204)


@router.delete("/friends/{friend_id}", status_code=204)
def remove_friend(
    friend_id: int,
    child: Child = Depends(get_current_child),
    db: Session = Depends(get_db),
):
    friendship = db.query(Friendship).filter(
        ((Friendship.child_a_id == child.id) & (Friendship.child_b_id == friend_id)) |
        ((Friendship.child_a_id == friend_id) & (Friendship.child_b_id == child.id))
    ).first()
    if not friendship:
        raise HTTPException(404, "Friendship not found")
    db.delete(friendship)
    db.commit()
    return Response(status_code=204)
