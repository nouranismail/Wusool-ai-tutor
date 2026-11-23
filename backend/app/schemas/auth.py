from __future__ import annotations
from typing import Optional
from pydantic import BaseModel, Field
from backend.app.schemas.common import AccessibilitySettings


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------

class ParentRegisterInput(BaseModel):
    name: str = Field(..., min_length=1)
    email: str = Field(..., min_length=5)
    password: str = Field(..., min_length=6)


class ChildRegisterInput(BaseModel):
    name: str = Field(..., min_length=1)
    username: str = Field(..., min_length=2, max_length=50, pattern=r"^[a-zA-Z0-9_]+$")
    grade: int = Field(..., ge=1, le=12)
    lang: str = Field(default="ar")
    accessibility: AccessibilitySettings = Field(default_factory=AccessibilitySettings)


class RegisterRequest(BaseModel):
    parent: ParentRegisterInput
    child: ChildRegisterInput


# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------

class LoginRequest(BaseModel):
    email: str
    password: str


# ---------------------------------------------------------------------------
# Child select / switch
# ---------------------------------------------------------------------------

class SelectChildRequest(BaseModel):
    parentPassword: Optional[str] = None  # Required only when switching with a child token


# ---------------------------------------------------------------------------
# Shared output shapes
# ---------------------------------------------------------------------------

class ParentOut(BaseModel):
    id: int
    name: str
    email: str
    role: str = "parent"


class AccessibilityOut(BaseModel):
    dyslexiaFont: bool
    highContrast: bool
    readAloud: bool


class ChildOut(BaseModel):
    id: int
    name: str
    username: str
    grade: int
    role: str = "child"
    lang: str
    accessibility: AccessibilitySettings


class ChildSummary(BaseModel):
    """Lightweight child info used in login response list."""
    id: int
    name: str
    username: str
    grade: int
    accessibility: AccessibilitySettings


# ---------------------------------------------------------------------------
# Response bodies
# ---------------------------------------------------------------------------

class RegisterResponse(BaseModel):
    parentToken: str
    childToken: str
    parent: ParentOut
    child: ChildOut


class LoginResponse(BaseModel):
    parentToken: str
    parent: ParentOut
    children: list[ChildSummary]


class SelectChildResponse(BaseModel):
    token: str
    user: ChildOut


class UsernameCheckResponse(BaseModel):
    available: bool
