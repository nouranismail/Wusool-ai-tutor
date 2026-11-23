"""
Pydantic request and response schemas for the /v1/ask endpoint.

Naming conventions
------------------
* AskRequest  – what the client sends
* SourceItem  – a single curriculum source reference
* AskResponse – what the API returns

These models are intentionally decoupled from any AI or RAG
implementation so that other engineers can integrate without
touching the HTTP layer.
"""

from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Request model
# ---------------------------------------------------------------------------


class AskRequest(BaseModel):
    """Payload sent by the client (frontend or voice pipeline) to /v1/ask."""

    question: str = Field(
        ...,
        min_length=1,
        description="The student's question in natural language.",
        examples=["ما هو الحاسوب؟"],
    )
    grade: Optional[str] = Field(
        default=None,
        description="Student's school grade, e.g. '3' or '4'.",
        examples=["3"],
    )
    subject: Optional[str] = Field(
        default=None,
        description="Curriculum subject, e.g. 'math' or 'cs'.",
        examples=["cs"],
    )
    language: str = Field(
        default="ar",
        description="Response language code (ISO 639-1).",
        examples=["ar", "en"],
    )
    input_mode: Literal["text", "voice"] = Field(
        default="text",
        description="How the question was submitted.",
    )
    mode: Literal["explain", "simplify", "summarize", "quiz", "repeat"] = Field(
        default="explain",
        description="Pedagogical mode for the tutor's response.",
    )
    session_id: Optional[str] = Field(
        default=None,
        description="Opaque session identifier for multi-turn tracking (future use).",
        examples=["sess_abc123"],
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "question": "ما هو الحاسوب؟",
                "grade": "3",
                "subject": "cs",
                "language": "ar",
                "input_mode": "text",
                "mode": "explain",
                "session_id": None,
            }
        }
    }


# ---------------------------------------------------------------------------
# Response models
# ---------------------------------------------------------------------------


class SourceItem(BaseModel):
    """A single curriculum source reference returned with an answer."""

    book: Optional[str] = Field(default=None, description="Textbook title.")
    lesson: Optional[str] = Field(default=None, description="Lesson name or number.")
    page: Optional[int] = Field(default=None, description="Page number in the book.")
    chunk_id: Optional[str] = Field(
        default=None, description="Unique identifier of the retrieved text chunk."
    )


class AskResponse(BaseModel):
    """Structured API response returned by /v1/ask."""

    status: Literal[
        "success", "no_answer", "out_of_scope", "low_confidence_input", "error"
    ] = Field(description="Outcome classification of the request.")
    answer: str = Field(description="Text answer suitable for display.")
    spoken_answer: Optional[str] = Field(
        default=None,
        description=(
            "TTS-ready version of the answer (future: Engineer 5 integration). "
            "May differ from `answer` to improve prosody."
        ),
    )
    sources: list[SourceItem] = Field(
        default_factory=list,
        description="Curriculum sources that informed the answer (future: RAG Engine).",
    )
    confidence: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Model confidence score in [0, 1] (future: AI Core).",
    )
    latency_ms: Optional[float] = Field(
        default=None,
        description="End-to-end processing time in milliseconds.",
    )
