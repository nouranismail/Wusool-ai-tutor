"""
POST  /api/children       — Add another child profile (after registration)
PATCH /api/me/settings    — Update child accessibility / language settings
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.core.dependencies import get_db, get_current_child, get_current_child_with_parent
from backend.app.core.security import verify_password
from backend.app.db.models.child import Child
from backend.app.db.models.progress import Progress
from backend.app.schemas.child import AddChildRequest, AddChildResponse, UpdateSettingsRequest, UpdateSettingsResponse
from backend.app.schemas.common import AccessibilitySettings

router = APIRouter()


@router.post("/children", response_model=AddChildResponse, status_code=201)
def add_child(
    body: AddChildRequest,
    child_and_parent: tuple = Depends(get_current_child_with_parent),
    db: Session = Depends(get_db),
):
    _current_child, parent = child_and_parent

    if not verify_password(body.parentPassword, parent.hashed_password):
        raise HTTPException(401, "Incorrect parent password")

    if body.grade not in settings.supported_grades:
        raise HTTPException(400, f"Grade must be one of {settings.supported_grades}")

    if db.query(Child).filter(Child.username == body.username).first():
        raise HTTPException(409, "Username already taken")

    acc = body.accessibility
    child = Child(
        parent_id=parent.id,
        name=body.name,
        username=body.username,
        grade=body.grade,
        lang=body.lang,
        dyslexia_font=acc.dyslexiaFont,
        high_contrast=acc.highContrast,
        read_aloud=acc.readAloud,
    )
    db.add(child)
    db.flush()
    db.add(Progress(child_id=child.id))
    db.commit()
    db.refresh(child)

    return AddChildResponse(
        id=child.id,
        name=child.name,
        username=child.username,
        grade=child.grade,
        lang=child.lang,
        accessibility=AccessibilitySettings(
            dyslexiaFont=child.dyslexia_font,
            highContrast=child.high_contrast,
            readAloud=child.read_aloud,
        ),
    )


@router.patch("/me/settings", response_model=UpdateSettingsResponse)
def update_settings(
    body: UpdateSettingsRequest,
    child: Child = Depends(get_current_child),
    db: Session = Depends(get_db),
):
    if body.dyslexiaFont is not None:
        child.dyslexia_font = body.dyslexiaFont
    if body.highContrast is not None:
        child.high_contrast = body.highContrast
    if body.readAloud is not None:
        child.read_aloud = body.readAloud
    if body.lang is not None:
        child.lang = body.lang
    db.commit()
    db.refresh(child)

    return UpdateSettingsResponse(
        dyslexiaFont=child.dyslexia_font,
        highContrast=child.high_contrast,
        readAloud=child.read_aloud,
        lang=child.lang,
    )
