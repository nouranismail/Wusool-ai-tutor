from __future__ import annotations
import json
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[3]
CURRICULUM_PATH = ROOT_DIR / "data" / "reviewed" / "curriculum.json"
MISCONCEPTIONS_PATH = ROOT_DIR / "data" / "misconceptions" / "math_grade2_misconceptions.json"


def lesson_chunks(lesson: dict) -> list[dict]:
    """تحويل درس واحد وأسئلته إلى قائمة أجزاء (Chunks) متوافقة مع الـ JSON المعتمد."""
    lesson_id = lesson.get("lesson_id", lesson.get("id", "unknown"))
    title = lesson.get("title", lesson.get("title_ar", ""))
    summary = lesson.get("summary", lesson.get("explanation_ar", ""))
    subject = lesson.get("subject", "general")
    source = lesson.get("source", {"file": "curriculum.json", "pages": [1]})

    common = {
        "lesson_id": lesson_id,
        "subject": subject,
        "title": title,
        "source_file": source.get("file", "curriculum.json"),
        "pages": source.get("pages", [1]),
    }

    # الجزء الخاص بالشرح والملخص
    explanation = {
        **common,
        "id": f"{lesson_id}:explanation",
        "kind": "explanation",
        "text_ar": f"درس: {title}. {summary}",
    }

    # الأجزاء الخاصة بالأسئلة للدرس
    questions = []
    for question in lesson.get("questions", []):
        q_id = question.get("question_id", question.get("id", "q"))
        q_text = question.get("text", question.get("question_ar", ""))
        correct = question.get("correct_answer", "")
        acceptable = ", ".join(question.get("acceptable_answers", []))

        questions.append({
            **common,
            "id": f"{lesson_id}:question:{q_id}",
            "kind": "assessment",
            "question_id": q_id,
            "text_ar": f"سؤال: {q_text} الإجابة الصحيحة: {correct} إجابات مقبولة: {acceptable}",
            "correct_answer": correct,
            "acceptable_answers": question.get("acceptable_answers", []),
        })

    return [explanation, *questions]


def load_all_chunks() -> list[dict]:
    """قراءة كل ملفات المنهج والمفاهيم الخاطئة وتجميع الـ Chunks."""
    all_chunks = []

    # 1. تحميل المنهج المراجع
    if CURRICULUM_PATH.exists():
        with open(CURRICULUM_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
            lessons = data.get("lessons", []) if isinstance(data, dict) else data
            for lesson in lessons:
                all_chunks.extend(lesson_chunks(lesson))

    # 2. تحميل المفاهيم الخاطئة (Misconceptions)
    if MISCONCEPTIONS_PATH.exists():
        with open(MISCONCEPTIONS_PATH, "r", encoding="utf-8") as f:
            misc_data = json.load(f)
            misc_list = misc_data.get("misconceptions", []) if isinstance(misc_data, dict) else misc_data
            for misc in misc_list:
                all_chunks.append({
                    "lesson_id": "misconception",
                    "subject": "math",
                    "title": "خطأ شائع",
                    "source_file": "math_grade2_misconceptions.json",
                    "pages": [1],
                    "id": f"misconception:{misc.get('id', '')}",
                    "kind": "misconception",
                    "text_ar": f"خطأ شائع: {misc.get('description', '')} التصحيح: {misc.get('correction', '')}",
                })

    return all_chunks