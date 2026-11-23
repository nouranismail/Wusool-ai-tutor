"""
FastAPI dependency functions for authentication and DB session injection.
"""
from __future__ import annotations

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.core.security import decode_token
from backend.app.db.session import SessionLocal

_bearer = HTTPBearer()


# ---------------------------------------------------------------------------
# Database session
# ---------------------------------------------------------------------------

def get_db():
    """Yield a SQLAlchemy Session, closing it when the request is done."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _extract_payload(credentials: HTTPAuthorizationCredentials) -> dict:
    try:
        return decode_token(credentials.credentials)
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )


# ---------------------------------------------------------------------------
# Public auth dependencies
# ---------------------------------------------------------------------------

def get_current_parent(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),
    db: Session = Depends(get_db),
):
    """Require a valid Parent JWT."""
    from backend.app.db.models.parent import Parent

    payload = _extract_payload(credentials)
    if payload.get("type") != "parent":
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Parent token required")
    parent = db.query(Parent).filter(Parent.id == int(payload["sub"])).first()
    if not parent:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Parent not found")
    return parent


def get_current_child(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),
    db: Session = Depends(get_db),
):
    """Require a valid Child JWT."""
    from backend.app.db.models.child import Child

    payload = _extract_payload(credentials)
    if payload.get("type") != "child":
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Child token required")
    child = db.query(Child).filter(Child.id == int(payload["sub"])).first()
    if not child:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Child not found")
    return child


def get_current_child_with_parent(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),
    db: Session = Depends(get_db),
):
    """Return (child, parent) tuple. Used where both are needed."""
    from backend.app.db.models.child import Child
    from backend.app.db.models.parent import Parent

    payload = _extract_payload(credentials)
    if payload.get("type") != "child":
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Child token required")
    child = db.query(Child).filter(Child.id == int(payload["sub"])).first()
    if not child:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Child not found")
    parent = db.query(Parent).filter(Parent.id == child.parent_id).first()
    if not parent:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Parent not found")
    return child, parent


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),
    db: Session = Depends(get_db),
):
    """Accept either a parent or child token. Used by GET /api/me."""
    from backend.app.db.models.child import Child
    from backend.app.db.models.parent import Parent

    payload = _extract_payload(credentials)
    token_type = payload.get("type")
    if token_type == "parent":
        user = db.query(Parent).filter(Parent.id == int(payload["sub"])).first()
    elif token_type == "child":
        user = db.query(Child).filter(Child.id == int(payload["sub"])).first()
    else:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid token type")
    if not user:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "User not found")
    return user


def get_admin(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),
) -> bool:
    """Verify the static admin token defined in .env."""
    if credentials.credentials != settings.admin_token:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Admin access required")
    return True


def decode_ws_token(token: str, db: Session):
    """Decode a WebSocket token (passed as ?token= query param). Returns Child."""
    from backend.app.db.models.child import Child

    try:
        payload = decode_token(token)
    except JWTError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid WS token")
    if payload.get("type") != "child":
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Child token required for WebSocket")
    child = db.query(Child).filter(Child.id == int(payload["sub"])).first()
    if not child:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Child not found")
    return child
