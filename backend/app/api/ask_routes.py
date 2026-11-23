"""
API route for the /v1/ask endpoint.

The handler's only responsibilities are:
  1. Accept the validated request body.
  2. Delegate to the orchestrator.
  3. Return the structured response.
  4. Surface any unexpected errors as HTTP 500.

No business logic lives here.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from backend.app.models.ask import AskRequest, AskResponse
from backend.app.services.orchestrator import handle_ask

router = APIRouter()


@router.post(
    "/ask",
    response_model=AskResponse,
    summary="Ask the AI tutor a question",
    description=(
        "Submit a student question and receive a structured educational answer. "
        "Supports both text and voice input modes, multiple pedagogical modes "
        "(explain, simplify, summarize, quiz, repeat), and Arabic / English responses."
    ),
    response_description="Structured tutor response with answer, sources, and metadata.",
    status_code=status.HTTP_200_OK,
)
def ask(request: AskRequest) -> AskResponse:
    """
    POST /v1/ask

    Accepts a student question and returns an AI-generated educational answer.
    Request validation is handled automatically by Pydantic/FastAPI.
    """
    try:
        return handle_ask(request)
    except Exception as exc:  # pragma: no cover – unexpected errors only
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An internal error occurred: {exc}",
        ) from exc
