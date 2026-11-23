"""
POST /api/study/lesson
POST /api/study/explain
POST /api/study/exercises
GET  /api/lessons/{id}?lang=
POST /api/exercises/{questionId}/check
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.app.core.dependencies import get_current_child, get_db
from backend.app.db.models.child import Child
from backend.app.schemas.study import (
    CheckAnswerRequest,
    CheckAnswerResponse,
    ExercisesRequest,
    ExercisesResponse,
    ExplainRequest,
    ExplainResponse,
    LessonContentResponse,
    LessonMatchRequest,
    LessonMatchResponse,
)
from backend.app.services.mock_data import (
    mock_check_answer,
    mock_exercises,
    mock_explain,
    mock_lesson_content,
    mock_lesson_match,
)

router = APIRouter()


@router.post("/study/lesson", response_model=LessonMatchResponse)
def find_lesson(
    body: LessonMatchRequest,
    _: Child = Depends(get_current_child),
):
    return mock_lesson_match(body.subject, body.query, body.lang)


@router.post("/study/explain", response_model=ExplainResponse)
def explain_lesson(
    body: ExplainRequest,
    _: Child = Depends(get_current_child),
):
    return mock_explain(body.lessonId, body.lang)


@router.post("/study/exercises", response_model=ExercisesResponse)
def get_exercises(
    body: ExercisesRequest,
    _: Child = Depends(get_current_child),
):
    return mock_exercises(body.lessonId, body.count)


@router.get("/lessons/{lesson_id}", response_model=LessonContentResponse)
def get_lesson(
    lesson_id: str,
    lang: str = Query(default="ar"),
    _: Child = Depends(get_current_child),
):
    result = mock_lesson_content(lesson_id, lang)
    if result is None:
        raise HTTPException(404, f"Lesson '{lesson_id}' not found")
    return result


@router.post("/exercises/{question_id}/check", response_model=CheckAnswerResponse)
def check_answer(
    question_id: str,
    body: CheckAnswerRequest,
    _: Child = Depends(get_current_child),
):
    result = mock_check_answer(question_id, body.answerId)
    if result is None:
        raise HTTPException(404, f"Question '{question_id}' not found")
    return result
