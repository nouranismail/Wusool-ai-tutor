# Wusool AI Tutor 🔊

**Wusool** (وصول) is an AI-powered, voice-first inclusive educational platform designed for elementary school students with visual impairments and dyslexia. 

Focusing on 3rd and 4th-grade **Computer Science** and **Mathematics** curricula, Wusool translates textbooks into interactive auditory lessons, delivers explainable continuous assessments, and moderates collaborative group learning sessions between peers with diverse learning capabilities.

---

## 🌟 Key Features

* **Auditory Learning Conversion:** Dynamically converts textbook content and exercises into clear, expressive audio streams.
* **Explainable Assessment Logic:** Quizzes students verbally, evaluates responses against curriculum context, and explains the *why* behind any incorrect answer.
* **Inclusive Peer Group Sessions:**
  * Pairs visually impaired students with students who have dyslexia in real-time learning sessions.
  * Dynamically moderated by an AI tutor host.
  * When one student makes a mistake, the AI redirects the prompt to a peer with a complementary capability to explain the correct answer and reasoning.

---

## 🏗️ Repository Architecture & Team Responsibilities

```text
Wusool-ai-tutor/
├── data_pipeline/         # [Data Engineer] Curricula parsing & dataset creation
├── ai_voice/              # [Voice AI Engineer] STT, TTS, & audio processing
├── rag_engine/            # [RAG Engineer] Vector DB & curriculum retrieval
├── ai_core/               # [AI Brain Engineer] Prompts, evaluation logic, & group moderation
├── backend/               # [Backend Engineer] FastAPI orchestrator, routes, & DB models
├── frontend/              # [Frontend Engineer] Accessible voice-first UI components
└── tests/                 # Integration & unit tests
