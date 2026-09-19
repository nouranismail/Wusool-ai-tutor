from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from .rag.retriever import CurriculumRetriever


ROOT = Path(__file__).resolve().parents[2]
LESSONS_PATH = ROOT / "data" / "reviewed" / "curriculum.json"


class TutorRequest(BaseModel):
    subject: Literal["math", "ict"]
    query: str = Field(min_length=1, max_length=300)
    language: Literal["ar", "en"] = "ar"


class AnswerRequest(BaseModel):
    lesson_id: str
    question_id: str | None = None
    answer: str = Field(min_length=1, max_length=100)


def load_lessons() -> list[dict]:
    return json.loads(LESSONS_PATH.read_text(encoding="utf-8"))


LESSONS = load_lessons()
RETRIEVER = CurriculumRetriever(LESSONS_PATH, ROOT / "data" / "vector_db" / "curriculum.sqlite3")


def normalize(text: str) -> list[str]:
    text = re.sub(r"[^\w]+", " ", text.lower(), flags=re.UNICODE)
    return [token for token in text.split() if len(token) > 1]


def normalize_answer(text: str) -> str:
    text = text.strip().lower().translate(str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789"))
    return re.sub(r"[^\w]+", " ", text, flags=re.UNICODE).strip()


def retrieve(subject: str, query: str) -> dict:
    matches = RETRIEVER.search(query, subject, limit=3)
    if not matches:
        raise HTTPException(status_code=404, detail="No reviewed content for this subject yet")
    lesson_id = matches[0]["lesson_id"]
    lesson = next(item for item in LESSONS if item["id"] == lesson_id)
    return {**lesson, "retrieval_matches": matches}


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
        {"id": "ict", "name_ar": "مهارات الحاسب", "name_en": "ICT Literacy", "ready": True},
    ]


@app.get("/api/lessons")
def lessons(subject: Literal["math", "ict"]) -> list[dict]:
    return [
        {"id": item["id"], "title_ar": item["title_ar"], "title_en": item["title_en"], "review_status": item["review_status"]}
        for item in LESSONS
        if item["subject"] == subject
    ]


@app.post("/api/tutor")
def tutor(request: TutorRequest) -> dict:
    lesson = retrieve(request.subject, request.query)
    question = lesson["questions"][0]
    explanation = lesson["explanation_ar"] if request.language == "ar" else lesson["explanation_en"]
    return {
        "lesson_id": lesson["id"],
        "title": lesson[f"title_{request.language}"],
        "explanation": explanation,
        "question_id": question["id"],
        "question": question[f"question_{request.language}"],
        "source": lesson["source"],
        "review_status": lesson["review_status"],
        "citations": [
            {"title": match["title_ar"], "file": match["source_file"], "pages": match["pages"], "score": match["score"]}
            for match in lesson["retrieval_matches"]
        ],
    }


@app.post("/api/answer")
def answer(request: AnswerRequest) -> dict:
    lesson = next((item for item in LESSONS if item["id"] == request.lesson_id), None)
    if lesson is None:
        raise HTTPException(status_code=404, detail="Lesson not found")
    question = next(
        (item for item in lesson["questions"] if request.question_id is None or item["id"] == request.question_id),
        None,
    )
    if question is None:
        raise HTTPException(status_code=404, detail="Question not found")
    normalized = normalize_answer(request.answer)
    correct = any(normalize_answer(candidate) == normalized for candidate in question["accepted_answers"])
    return {
        "correct": correct,
        "feedback_ar": "إجابة رائعة! أحسنت." if correct else question["hint_ar"],
        "feedback_en": "Great answer! Well done." if correct else question["hint_en"],
    }


app.mount("/assets", StaticFiles(directory=ROOT / "frontend"), name="assets")


@app.get("/")
def index() -> FileResponse:
    return FileResponse(ROOT / "frontend" / "index.html")
