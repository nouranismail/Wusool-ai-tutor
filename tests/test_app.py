from backend.app.main import normalize, retrieve


def test_arabic_retrieval_finds_multiplication_lesson():
    lesson = retrieve("math", "اشرح لي خواص الضرب")
    assert lesson["id"] == "math-multiplication-properties"


def test_normalize_keeps_arabic_terms():
    assert "الضرب" in normalize("ما هي خواص الضرب؟")

