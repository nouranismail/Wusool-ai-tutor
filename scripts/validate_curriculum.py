import json
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
CURRICULUM_PATH = ROOT_DIR / "data" / "reviewed" / "curriculum.json"

def validate():
    if not CURRICULUM_PATH.exists():
        raise FileNotFoundError(f"Curriculum file not found at {CURRICULUM_PATH}")

    with open(CURRICULUM_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    lessons = data.get("lessons", []) if isinstance(data, dict) else data
    total_questions = 0

    for lesson in lessons:
        lesson_id = lesson.get("lesson_id") or lesson.get("id")
        assert lesson_id, "Each lesson must have a 'lesson_id' or 'id'"

        title = lesson.get("title") or lesson.get("title_ar")
        assert title, f"Lesson {lesson_id} missing title"

        questions = lesson.get("questions", [])
        total_questions += len(questions)

        for q in questions:
            q_id = q.get("question_id") or q.get("id")
            assert q_id, f"Question in lesson {lesson_id} missing ID"

    print(f"Validated {len(lessons)} lessons and {total_questions} questions successfully!")
    return len(lessons), total_questions

if __name__ == "__main__":
    validate()