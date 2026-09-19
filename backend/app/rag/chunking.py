from __future__ import annotations


def lesson_chunks(lesson: dict) -> list[dict]:
    common = {
        "lesson_id": lesson["id"],
        "subject": lesson["subject"],
        "title_ar": lesson["title_ar"],
        "source_file": lesson["source"]["file"],
        "pages": lesson["source"]["pages"],
        "review_status": lesson["review_status"],
    }
    explanation = {
        **common,
        "id": f"{lesson['id']}:explanation",
        "kind": "explanation",
        "text_ar": f"{lesson['title_ar']}. {lesson['explanation_ar']} كلمات الدرس: {' '.join(lesson['keywords'])}",
    }
    questions = [
        {
            **common,
            "id": f"{lesson['id']}:question:{question['id']}",
            "kind": "assessment",
            "text_ar": f"{lesson['title_ar']}. {question['question_ar']} {question['hint_ar']}",
        }
        for question in lesson["questions"]
    ]
    return [explanation, *questions]

