"""
Orchestrator service – the single entry-point for the ask flow.

Architecture
------------
Route handler → orchestrator.handle_ask() → (future) RAG + AI Core → response

The route handler never contains business logic.  When Engineer 3 (RAG Engine)
and Engineer 4 (AI Core) are ready, only the internals of `handle_ask` change;
the function signature and return type remain stable.

Current state: returns a deterministic mock response so the full HTTP pipeline
can be verified end-to-end without real AI dependencies.
"""

from __future__ import annotations

import time

from backend.app.models.ask import AskRequest, AskResponse, SourceItem

# ---------------------------------------------------------------------------
# Mock response bank
# ---------------------------------------------------------------------------

_MOCK_ANSWERS: dict[str, str] = {
    "explain": (
        "هذا شرح تجريبي للسؤال الذي طرحته. "
        "سيتم استبداله بإجابة حقيقية من محرك الاسترجاع والذكاء الاصطناعي."
    ),
    "simplify": (
        "إجابة مبسطة: سيتم ربط هذه الخدمة بمحرك الذكاء الاصطناعي لاحقاً."
    ),
    "summarize": (
        "ملخص: هذه استجابة تجريبية. سيتم توليد الملخصات الحقيقية بواسطة المعالج اللغوي."
    ),
    "quiz": (
        "سؤال اختبار: ما هو الجزء الرئيسي من الحاسوب؟ "
        "(هذا سؤال تجريبي – سيأتي المحتوى الحقيقي من قاعدة المعرفة)"
    ),
    "repeat": (
        "إعادة: سيتم تكرار الإجابة السابقة هنا عند تكامل إدارة الجلسات."
    ),
}


# ---------------------------------------------------------------------------
# Public interface
# ---------------------------------------------------------------------------


def handle_ask(request: AskRequest) -> AskResponse:
    """
    Orchestrate the question-answering flow for a single student request.

    Parameters
    ----------
    request:
        Validated AskRequest from the HTTP layer.

    Returns
    -------
    AskResponse
        Structured response ready for serialisation.

    Integration points (not yet implemented)
    ----------------------------------------
    * RAG Engine  (Engineer 3): replace ``_mock_retrieve()`` call
    * AI Core     (Engineer 4): replace ``_mock_generate()`` call
    * Voice/TTS   (Engineer 5): populate ``spoken_answer`` from TTS pipeline
    """
    start = time.perf_counter()

    # -- Step 1: Retrieve relevant curriculum context (stubbed) --
    sources = _mock_retrieve(request)

    # -- Step 2: Generate answer (stubbed) --
    answer = _mock_generate(request)

    latency_ms = (time.perf_counter() - start) * 1000

    return AskResponse(
        status="success",
        answer=answer,
        spoken_answer=None,  # Engineer 5 will populate this
        sources=sources,
        confidence=None,     # Engineer 4 will populate this
        latency_ms=round(latency_ms, 2),
    )


# ---------------------------------------------------------------------------
# Private stubs – replace with real implementations during integration
# ---------------------------------------------------------------------------


def _mock_retrieve(request: AskRequest) -> list[SourceItem]:
    """
    Stub for the RAG retrieval step.

    Engineer 3: replace the body of this function (or remove it entirely and
    call the RAG engine directly from ``handle_ask``).
    """
    if request.subject and request.grade:
        return [
            SourceItem(
                book=f"كتاب {request.subject} للصف {request.grade}",
                lesson="الوحدة الأولى",
                page=1,
                chunk_id="mock-chunk-001",
            )
        ]
    return []


def _mock_generate(request: AskRequest) -> str:
    """
    Stub for the LLM generation step.

    Engineer 4: replace the body of this function (or remove it entirely and
    call the AI Core directly from ``handle_ask``).
    """
    template = _MOCK_ANSWERS.get(request.mode, _MOCK_ANSWERS["explain"])
    return f"[{request.mode.upper()}] {template}"
