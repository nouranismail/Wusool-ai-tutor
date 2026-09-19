from backend.app.main import normalize, normalize_answer, retrieve
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
