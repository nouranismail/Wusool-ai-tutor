"""JWT token creation/verification and password hashing.

Token payload structure:
  Parent token: {"sub": "<parent_id>", "type": "parent", "exp": ...}
  Child token:  {"sub": "<child_id>",  "type": "child",  "parent_id": "<parent_id>", "exp": ...}
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext

from backend.app.core.config import settings

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ---------------------------------------------------------------------------
# Password utilities
# ---------------------------------------------------------------------------

def hash_password(plain: str) -> str:
    return _pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    return _pwd_context.verify(plain, hashed)


# ---------------------------------------------------------------------------
# Token utilities
# ---------------------------------------------------------------------------

def _create_token(data: dict[str, Any], expires_delta: timedelta | None = None) -> str:
    payload = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.access_token_expire_minutes)
    )
    payload["exp"] = expire
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def create_parent_token(parent_id: int) -> str:
    return _create_token({"sub": str(parent_id), "type": "parent"})


def create_child_token(child_id: int, parent_id: int) -> str:
    return _create_token(
        {"sub": str(child_id), "type": "child", "parent_id": str(parent_id)}
    )


def decode_token(token: str) -> dict[str, Any]:
    """Decode and return raw payload. Raises JWTError on failure."""
    return jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
