from __future__ import annotations
from typing import Optional
from pydantic import BaseModel, Field


class LessonMatchRequest(BaseModel):
    subject: str
    query: str
    lang: str = "ar"


class LessonRef(BaseModel):
    id: str
    title: str


class LessonMatchResponse(BaseModel):
    found: bool
    lesson: Optional[LessonRef] = None
    suggestions: Optional[list[LessonRef]] = None


class ExplainRequest(BaseModel):
    lessonId: str
    subject: str
    lang: str = "ar"


class ExplainSection(BaseModel):
    heading: str
    text: str


class ExplainResponse(BaseModel):
    title: str
    sections: list[ExplainSection]


class ExercisesRequest(BaseModel):
    lessonId: str
    subject: str
    lang: str = "ar"
    count: int = Field(default=3, ge=1, le=20)


class OptionOut(BaseModel):
    id: str
    label: str


class QuestionOut(BaseModel):
    questionId: str
    question: str
    options: list[OptionOut]


class ExercisesResponse(BaseModel):
    questions: list[QuestionOut]


class LessonContentResponse(BaseModel):
    id: str
    title: str
    sentences: list[str]
    example: str
    exercises: list[QuestionOut]


class CheckAnswerRequest(BaseModel):
    answerId: str


class CheckAnswerResponse(BaseModel):
    correct: bool
    feedback: str
