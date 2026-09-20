from backend.app.main import LESSONS, RETRIEVER, retrieve


def test_vector_index_contains_explanation_and_question_chunks():
    RETRIEVER.ensure_index()
    with __import__("sqlite3").connect(RETRIEVER.store.path) as connection:
        count = connection.execute("SELECT COUNT(*) FROM chunks").fetchone()[0]
    assert count == len(LESSONS) + sum(len(lesson["questions"]) for lesson in LESSONS)


def test_math_missing_number_retrieval():
    lesson = retrieve("math", "كيف أجد العدد الناقص في جدول الضرب؟")
    assert lesson["id"] == "math-missing-number"
    assert lesson["retrieval_matches"][0]["source_file"] == "IMG_9540.pdf"


def test_ict_input_output_retrieval():
    lesson = retrieve("ict", "ما الفرق بين المدخلات والمخرجات؟")
    assert lesson["id"] == "ict-input-output"
    assert lesson["retrieval_matches"][0]["pages"] == [2]


def test_subject_filter_prevents_cross_subject_results():
    results = RETRIEVER.search("الكمبيوتر والمدخلات", "math", limit=5)
    assert results
    assert {item["subject"] for item in results} == {"math"}
