"""Shared schema types reused across multiple endpoints."""
from __future__ import annotations
from pydantic import BaseModel


class AccessibilitySettings(BaseModel):
    """
    Replaces the old accessibilityNeed string field everywhere — both on input and output.
    The frontend is responsible for mapping its UI state to these three boolean flags.
    """
    dyslexiaFont: bool = False
    highContrast: bool = False
    readAloud: bool = False
