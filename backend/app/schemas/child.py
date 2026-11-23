from __future__ import annotations
from typing import Optional
from pydantic import BaseModel, Field
from backend.app.schemas.common import AccessibilitySettings


class AddChildRequest(BaseModel):
    name: str = Field(..., min_length=1)
    username: str = Field(..., min_length=2, max_length=50, pattern=r"^[a-zA-Z0-9_]+$")
    grade: int = Field(..., ge=1, le=12)
    lang: str = Field(default="ar")
    accessibility: AccessibilitySettings = Field(default_factory=AccessibilitySettings)
    parentPassword: str


class AddChildResponse(BaseModel):
    id: int
    name: str
    username: str
    grade: int
    lang: str
    accessibility: AccessibilitySettings


class UpdateSettingsRequest(BaseModel):
    dyslexiaFont: Optional[bool] = None
    highContrast: Optional[bool] = None
    readAloud: Optional[bool] = None
    lang: Optional[str] = None


class UpdateSettingsResponse(BaseModel):
    dyslexiaFont: bool
    highContrast: bool
    readAloud: bool
    lang: str
