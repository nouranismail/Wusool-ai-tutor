"""
Centralised mock data for all AI / RAG / Voice endpoints.

When Engineer 3 (RAG Engine), Engineer 4 (AI Core), and Engineer 5 (Voice)
are ready, replace the bodies of these functions — the route handlers
do not need to change.
"""
from __future__ import annotations

from backend.app.schemas.study import (
    LessonRef,
    LessonMatchResponse,
    ExplainResponse,
    ExplainSection,
    ExercisesResponse,
    QuestionOut,
    OptionOut,
    LessonContentResponse,
    CheckAnswerResponse,
)
from backend.app.schemas.chat import SendMessageResponse, ChatSource
from backend.app.schemas.voice import STTResponse, VoiceChatResponse
from backend.app.schemas.session import SessionOut, ParticipantOut

# ---------------------------------------------------------------------------
# Lesson catalogue
# ---------------------------------------------------------------------------

_LESSONS: dict[str, dict] = {
    "animals":      {"id": "animals",      "title": "Favourite Animals",        "subject": "english", "grade": 3},
    "pets":         {"id": "pets",         "title": "Pets and Care",            "subject": "english", "grade": 3},
    "wild_animals": {"id": "wild_animals", "title": "Wild Animals",             "subject": "english", "grade": 4},
    "space":        {"id": "space",        "title": "Space Adventure",          "subject": "english", "grade": 4},
    "vocab":        {"id": "vocab",        "title": "Vocabulary Practice",      "subject": "english", "grade": 3},
    "ict-1":        {"id": "ict-1",        "title": "Introduction to Computers","subject": "ict",     "grade": 3},
    "ict-2":        {"id": "ict-2",        "title": "Parts of a Computer",      "subject": "ict",     "grade": 3},
    "ict-3":        {"id": "ict-3",        "title": "How does the internet work?","subject": "ict",   "grade": 4},
}

# ---------------------------------------------------------------------------
# Question bank (correct answers stored here — NEVER sent to client)
# ---------------------------------------------------------------------------

_QUESTIONS: dict[str, dict] = {
    "q_000001": {
        "lesson_id": "animals",
        "text": "What sound does a cat make?",
        "correct": "a",
        "options": [
            {"id": "a", "label": "Meow"},
            {"id": "b", "label": "Woof"},
            {"id": "c", "label": "Moo"},
        ],
    },
    "q_000002": {
        "lesson_id": "animals",
        "text": "Which animal is the largest?",
        "correct": "c",
        "options": [
            {"id": "a", "label": "Dog"},
            {"id": "b", "label": "Cat"},
            {"id": "c", "label": "Elephant"},
        ],
    },
    "q_000003": {
        "lesson_id": "animals",
        "text": "Where do fish live?",
        "correct": "b",
        "options": [
            {"id": "a", "label": "In trees"},
            {"id": "b", "label": "In water"},
            {"id": "c", "label": "Underground"},
        ],
    },
    "q_000050": {
        "lesson_id": "ict-1",
        "text": "What is a computer?",
        "correct": "a",
        "options": [
            {"id": "a", "label": "An electronic device that processes information"},
            {"id": "b", "label": "A type of phone"},
            {"id": "c", "label": "A musical instrument"},
        ],
    },
    "q_000120": {
        "lesson_id": "ict-3",
        "text": "What is a router?",
        "correct": "a",
        "options": [
            {"id": "a", "label": "A device that directs network traffic"},
            {"id": "b", "label": "A type of screen"},
        ],
    },
    "q_000121": {
        "lesson_id": "ict-3",
        "text": "What does HTTP stand for?",
        "correct": "b",
        "options": [
            {"id": "a", "label": "High Transfer Text Protocol"},
            {"id": "b", "label": "HyperText Transfer Protocol"},
            {"id": "c", "label": "Home Tool Transfer Protocol"},
        ],
    },
}

_LESSON_QUESTIONS: dict[str, list[str]] = {
    "animals":  ["q_000001", "q_000002", "q_000003"],
    "ict-1":    ["q_000050"],
    "ict-3":    ["q_000120", "q_000121"],
}

_ALL_QUESTION_IDS = list(_QUESTIONS.keys())


# ---------------------------------------------------------------------------
# Public mock functions
# ---------------------------------------------------------------------------

def mock_lesson_match(subject: str, query: str, lang: str) -> LessonMatchResponse:
    q = query.lower()
    for lesson in _LESSONS.values():
        if lesson["subject"] == subject and q in lesson["id"].lower():
            return LessonMatchResponse(
                found=True,
                lesson=LessonRef(id=lesson["id"], title=lesson["title"]),
            )
    suggestions = [
        LessonRef(id=l["id"], title=l["title"])
        for l in _LESSONS.values()
        if l["subject"] == subject
    ][:2]
    return LessonMatchResponse(found=False, suggestions=suggestions)


def mock_explain(lesson_id: str, lang: str) -> ExplainResponse:
    lesson = _LESSONS.get(lesson_id)
    title = lesson["title"] if lesson else lesson_id
    if lang == "ar":
        sections = [
            ExplainSection(
                heading="الفكرة الأساسية",
                text=f"هذا شرح تجريبي للدرس: {title}. سيتم استبداله بمحتوى حقيقي من محرك RAG.",
            ),
            ExplainSection(
                heading="مثال",
                text="مثال بسيط من الحياة اليومية يوضح المفهوم بطريقة سهلة.",
            ),
        ]
    else:
        sections = [
            ExplainSection(
                heading="Main Idea",
                text=f"This is a mock explanation for: {title}. Will be replaced by real RAG content.",
            ),
            ExplainSection(
                heading="Example",
                text="A simple real-life example that illustrates the concept clearly.",
            ),
        ]
    return ExplainResponse(title=title, sections=sections)


def mock_exercises(lesson_id: str, count: int) -> ExercisesResponse:
    qids = _LESSON_QUESTIONS.get(lesson_id, _ALL_QUESTION_IDS)[:count]
    questions = []
    for qid in qids:
        q = _QUESTIONS.get(qid)
        if not q:
            continue
        questions.append(
            QuestionOut(
                questionId=qid,
                question=q["text"],
                options=[OptionOut(id=o["id"], label=o["label"]) for o in q["options"]],
            )
        )
    return ExercisesResponse(questions=questions)


def mock_lesson_content(lesson_id: str, lang: str) -> LessonContentResponse | None:
    lesson = _LESSONS.get(lesson_id)
    if not lesson:
        return None
    qids = _LESSON_QUESTIONS.get(lesson_id, [])
    exercises = []
    for qid in qids:
        q = _QUESTIONS.get(qid)
        if q:
            exercises.append(
                QuestionOut(
                    questionId=qid,
                    question=q["text"],
                    options=[OptionOut(id=o["id"], label=o["label"]) for o in q["options"]],
                )
            )
    if lang == "ar":
        sentences = [
            f"هذا هو الدرس: {lesson['title']}.",
            "سيتم ملء هذا المحتوى من قاعدة المعرفة عند تكامل محرك RAG.",
            "يرجى الانتظار حتى تكتمل عملية التكامل.",
        ]
        example = "مثال تجريبي من الحياة اليومية."
    else:
        sentences = [
            f"This is lesson: {lesson['title']}.",
            "Content will be populated from the knowledge base upon RAG integration.",
            "Please wait for the integration to complete.",
        ]
        example = "A sample real-life example for this lesson."
    return LessonContentResponse(
        id=lesson_id,
        title=lesson["title"],
        sentences=sentences,
        example=example,
        exercises=exercises,
    )


def mock_check_answer(question_id: str, answer_id: str) -> CheckAnswerResponse | None:
    q = _QUESTIONS.get(question_id)
    if not q:
        return None
    correct = q["correct"] == answer_id
    feedback = (
        "Great job! That's exactly right. 🎉"
        if correct
        else f"Not quite. Keep trying! Hint: think carefully about each option."
    )
    return CheckAnswerResponse(correct=correct, feedback=feedback)


def mock_chat_reply(
    message: str, lesson_id: str, conversation_id: str, lang: str
) -> SendMessageResponse:
    if lang == "ar":
        reply = (
            f"هذا رد تجريبي على سؤالك: '{message}'. "
            "سيتم استبداله برد حقيقي من الذكاء الاصطناعي."
        )
    else:
        reply = (
            f"This is a mock reply to your question: '{message}'. "
            "Will be replaced by a real AI response."
        )
    return SendMessageResponse(
        reply=reply,
        conversationId=conversation_id,
        sources=[
            ChatSource(
                title=f"Lesson — {lesson_id}",
                snippet="Mock snippet from the knowledge base...",
            )
        ],
    )


def mock_stt(lang: str) -> STTResponse:
    if lang == "ar":
        return STTResponse(text="كيف يعمل الإنترنت")
    return STTResponse(text="How does the internet work?")


def mock_voice_chat(lang: str) -> VoiceChatResponse:
    if lang == "ar":
        return VoiceChatResponse(
            transcript="كيف يعمل الإنترنت",
            reply="الإنترنت هو شبكة عالمية من الحواسيب المتصلة ببعضها. هذا رد تجريبي.",
            audioUrl=None,
        )
    return VoiceChatResponse(
        transcript="How does the internet work?",
        reply="The internet is a global network of connected computers. This is a mock reply.",
        audioUrl=None,
    )


def mock_ai_session_message(user_text: str) -> str:
    """Mock AI tutor reply for English sessions. ALWAYS responds in English."""
    return f"Great sentence! You said: '{user_text}'. Keep practicing your English!"
