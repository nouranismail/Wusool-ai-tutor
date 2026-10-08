from fastapi.testclient import TestClient

from backend.app.main import app, normalize, normalize_answer, retrieve
from scripts.validate_curriculum import validate


def test_arabic_retrieval_finds_multiplication_lesson():
    lesson = retrieve("math", "اشرح لي خواص الضرب")
    assert lesson["id"] == "math-properties-1"


def test_normalize_keeps_arabic_terms():
    assert "الضرب" in normalize("ما هي خواص الضرب؟")


def test_curriculum_has_both_subjects_and_sources():
    lessons = validate()
    assert {lesson["subject"] for lesson in lessons} == {"math", "ict"}
    assert all(lesson["source"]["pages"] for lesson in lessons)


def test_arabic_digits_are_normalized():
    assert normalize_answer("٧٠") == "70"


client = TestClient(app)


def test_tutor_returns_the_lesson_chosen_by_id():
    # Part one and part two have near-identical titles, so retrieval by title is not enough.
    response = client.post("/api/tutor", json={"subject": "math", "query": "x", "lesson_id": "math-properties-2"})
    assert response.status_code == 200
    body = response.json()
    assert body["lesson_id"] == "math-properties-2"
    assert body["citations"][0]["pages"]


def test_tutor_rejects_unknown_or_wrong_subject_lesson_id():
    unknown = client.post("/api/tutor", json={"subject": "math", "query": "x", "lesson_id": "nope"})
    wrong_subject = client.post("/api/tutor", json={"subject": "ict", "query": "x", "lesson_id": "math-properties-2"})
    assert unknown.status_code == 404
    assert wrong_subject.status_code == 404
