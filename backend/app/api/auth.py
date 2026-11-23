"""
Authentication & user management routes.

POST  /api/auth/register
POST  /api/auth/login
POST  /api/auth/children/{childId}/select
GET   /api/me
GET   /api/users/check-username
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.core.dependencies import get_db, get_current_user
from backend.app.core.security import (
    hash_password,
    verify_password,
    create_parent_token,
    create_child_token,
    decode_token,
)
from backend.app.db.models.child import Child
from backend.app.db.models.parent import Parent
from backend.app.db.models.progress import Progress
from backend.app.schemas.auth import (
    RegisterRequest,
    RegisterResponse,
    ParentOut,
    ChildOut,
    ChildSummary,
    LoginRequest,
    LoginResponse,
    SelectChildRequest,
    SelectChildResponse,
    UsernameCheckResponse,
)
from backend.app.schemas.common import AccessibilitySettings

router = APIRouter()
_bearer = HTTPBearer()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _child_to_out(child: Child) -> ChildOut:
    return ChildOut(
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


def _child_to_summary(child: Child) -> ChildSummary:
    return ChildSummary(
        id=child.id,
        name=child.name,
        username=child.username,
        grade=child.grade,
        accessibility=AccessibilitySettings(
            dyslexiaFont=child.dyslexia_font,
            highContrast=child.high_contrast,
            readAloud=child.read_aloud,
        ),
    )


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.post("/auth/register", response_model=RegisterResponse, status_code=201)
def register(body: RegisterRequest, db: Session = Depends(get_db)):
    if body.child.grade not in settings.supported_grades:
        raise HTTPException(400, f"Grade must be one of {settings.supported_grades}")

    if db.query(Parent).filter(Parent.email == body.parent.email).first():
        raise HTTPException(409, "Email already registered")

    if db.query(Child).filter(Child.username == body.child.username).first():
        raise HTTPException(409, "Username already taken")

    # Create parent and child atomically — if either fails, nothing is committed
    parent = Parent(
        name=body.parent.name,
        email=body.parent.email,
        hashed_password=hash_password(body.parent.password),
    )
    db.add(parent)
    db.flush()  # assign parent.id without committing

    acc = body.child.accessibility
    child = Child(
        parent_id=parent.id,
        name=body.child.name,
        username=body.child.username,
        grade=body.child.grade,
        lang=body.child.lang,
        dyslexia_font=acc.dyslexiaFont,
        high_contrast=acc.highContrast,
        read_aloud=acc.readAloud,
    )
    db.add(child)
    db.flush()

    db.add(Progress(child_id=child.id))
    db.commit()
    db.refresh(parent)
    db.refresh(child)

    return RegisterResponse(
        parentToken=create_parent_token(parent.id),
        childToken=create_child_token(child.id, parent.id),
        parent=ParentOut(id=parent.id, name=parent.name, email=parent.email),
        child=_child_to_out(child),
    )


@router.post("/auth/login", response_model=LoginResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)):
    parent = db.query(Parent).filter(Parent.email == body.email).first()
    if not parent or not verify_password(body.password, parent.hashed_password):
        raise HTTPException(401, "Invalid email or password")

    children = db.query(Child).filter(Child.parent_id == parent.id).all()
    return LoginResponse(
        parentToken=create_parent_token(parent.id),
        parent=ParentOut(id=parent.id, name=parent.name, email=parent.email),
        children=[_child_to_summary(c) for c in children],
    )


@router.post("/auth/children/{child_id}/select", response_model=SelectChildResponse)
def select_child(
    child_id: int,
    body: SelectChildRequest,
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),
    db: Session = Depends(get_db),
):
    try:
        payload = decode_token(credentials.credentials)
    except JWTError:
        raise HTTPException(401, "Invalid or expired token")

    token_type = payload.get("type")

    if token_type == "parent":
        # Initial selection after login — no extra password needed
        parent_id = int(payload["sub"])
    elif token_type == "child":
        # Profile switching — parent password required
        if not body.parentPassword:
            raise HTTPException(400, "parentPassword is required when switching profiles")
        current_child = db.query(Child).filter(Child.id == int(payload["sub"])).first()
        if not current_child:
            raise HTTPException(401, "Session invalid")
        parent = db.query(Parent).filter(Parent.id == current_child.parent_id).first()
        if not parent or not verify_password(body.parentPassword, parent.hashed_password):
            raise HTTPException(401, "Incorrect parent password")
        parent_id = parent.id
    else:
        raise HTTPException(401, "Invalid token type")

    child = db.query(Child).filter(
        Child.id == child_id, Child.parent_id == parent_id
    ).first()
    if not child:
        raise HTTPException(404, "Child not found or does not belong to this parent")

    return SelectChildResponse(
        token=create_child_token(child.id, parent_id),
        user=_child_to_out(child),
    )


@router.get("/me")
def get_me(current_user=Depends(get_current_user)):
    if isinstance(current_user, Parent):
        return {
            "id": current_user.id,
            "name": current_user.name,
            "email": current_user.email,
            "role": "parent",
        }
    # Child
    c = current_user
    return {
        "id": c.id,
        "name": c.name,
        "username": c.username,
        "grade": c.grade,
        "role": "child",
        "lang": c.lang,
        "accessibility": {
            "dyslexiaFont": c.dyslexia_font,
            "highContrast": c.high_contrast,
            "readAloud": c.read_aloud,
        },
    }


@router.get("/users/check-username", response_model=UsernameCheckResponse)
def check_username(
    u: str = Query(..., min_length=1),
    db: Session = Depends(get_db),
):
    taken = db.query(Child).filter(Child.username == u).first() is not None
    return UsernameCheckResponse(available=not taken)
