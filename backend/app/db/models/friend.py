from __future__ import annotations
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from backend.app.db.base import Base


class FriendRequest(Base):
    __tablename__ = "friend_requests"

    id = Column(Integer, primary_key=True)
    sender_id = Column(
        Integer,
        ForeignKey("children.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    recipient_id = Column(
        Integer,
        ForeignKey("children.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # pending_sender_parent | pending_recipient_parent | accepted | rejected | cancelled
    status = Column(String(50), nullable=False, default="pending_sender_parent")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class Friendship(Base):
    __tablename__ = "friendships"

    id = Column(Integer, primary_key=True)
    child_a_id = Column(
        Integer,
        ForeignKey("children.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    child_b_id = Column(
        Integer,
        ForeignKey("children.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
