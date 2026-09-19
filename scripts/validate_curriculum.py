from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CURRICULUM = ROOT / "data" / "reviewed" / "curriculum.json"
REQUIRED = {"id", "subject", "grade", "title_ar", "title_en", "keywords", "explanation_ar", "explanation_en", "questions", "source", "review_status"}


def validate() -> list[dict]:
    lessons = json.loads(CURRICULUM.read_text(encoding="utf-8"))
    assert isinstance(lessons, list) and lessons, "Curriculum must be a non-empty list"
    ids: set[str] = set()
    question_ids: set[str] = set()
    for lesson in lessons:
        missing = REQUIRED - set(lesson)
        assert not missing, f"{lesson.get('id', 'unknown')} missing {sorted(missing)}"
        assert lesson["id"] not in ids, f"Duplicate lesson id: {lesson['id']}"
        ids.add(lesson["id"])
        assert lesson["subject"] in {"math", "ict"}
        assert lesson["review_status"] in {"needs_owner_review", "approved"}
        assert lesson["source"]["pages"], f"{lesson['id']} has no source pages"
        assert lesson["questions"], f"{lesson['id']} has no questions"
        for question in lesson["questions"]:
            assert question["id"] not in question_ids, f"Duplicate question id: {question['id']}"
            question_ids.add(question["id"])
            assert question["accepted_answers"], f"{question['id']} has no accepted answers"
    return lessons


if __name__ == "__main__":
    items = validate()
    print(f"Validated {len(items)} lessons and {sum(len(item['questions']) for item in items)} questions")
