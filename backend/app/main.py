from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field


ROOT = Path(__file__).resolve().parents[2]
LESSONS_PATH = Path(__file__).with_name("lessons.json")


class TutorRequest(BaseModel):
    subject: Literal["math", "ict"]
    query: str = Field(min_length=1, max_length=300)
    language: Literal["ar", "en"] = "ar"


class AnswerRequest(BaseModel):
    lesson_id: str
    answer: str = Field(min_length=1, max_length=100)


def load_lessons() -> list[dict]:
    return json.loads(LESSONS_PATH.read_text(encoding="utf-8"))


LESSONS = load_lessons()


def normalize(text: str) -> list[str]:
    text = re.sub(r"[^\w]+", " ", text.lower(), flags=re.UNICODE)
    return [token for token in text.split() if len(token) > 1]


def retrieve(subject: str, query: str) -> dict:
    candidates = [lesson for lesson in LESSONS if lesson["subject"] == subject]
    if not candidates:
        raise HTTPException(status_code=404, detail="No reviewed content for this subject yet")
    query_terms = set(normalize(query))
    return max(
        candidates,
        key=lambda lesson: len(query_terms & set(normalize(" ".join(lesson["keywords"])))),
    )


app = FastAPI(
    title="Wusool AI Tutor API",
    description="Accessible, curriculum-grounded tutoring MVP.",
    version="0.1.0",
)


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok", "reviewed_lessons": len(LESSONS)}


@app.get("/api/subjects")
def subjects() -> list[dict]:
    return [
        {"id": "math", "name_ar": "الرياضيات", "name_en": "Math", "ready": True},
        {"id": "ict", "name_ar": "مهارات الحاسب", "name_en": "ICT Literacy", "ready": False},
    ]


@app.post("/api/tutor")
def tutor(request: TutorRequest) -> dict:
    lesson = retrieve(request.subject, request.query)
    explanation = lesson["explanation_ar"] if request.language == "ar" else lesson["explanation_en"]
    return {
        "lesson_id": lesson["id"],
        "title": lesson[f"title_{request.language}"],
        "explanation": explanation,
        "question": lesson[f"question_{request.language}"],
        "source": lesson["source"],
    }


@app.post("/api/answer")
def answer(request: AnswerRequest) -> dict:
    lesson = next((item for item in LESSONS if item["id"] == request.lesson_id), None)
    if lesson is None:
        raise HTTPException(status_code=404, detail="Lesson not found")
    correct = request.answer.strip().translate(str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")) == lesson["answer"]
    return {
        "correct": correct,
        "feedback_ar": "إجابة رائعة! أحسنت." if correct else lesson["hint_ar"],
        "feedback_en": "Great answer! Well done." if correct else lesson["hint_en"],
    }


app.mount("/assets", StaticFiles(directory=ROOT / "frontend"), name="assets")


@app.get("/")
def index() -> FileResponse:
    return FileResponse(ROOT / "frontend" / "index.html")
