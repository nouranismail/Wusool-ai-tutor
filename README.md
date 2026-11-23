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
```

---

## 🚀 Backend – Getting Started

### Prerequisites

- Python 3.11+ (project uses Python 3.14)
- A virtual environment at `.venv/` (already created in this repo)

### 1. Activate the virtual environment

```bash
# From the project root
source .venv/bin/activate
```

### 2. Install backend dependencies

```bash
pip install -r backend/requirements.txt
```

> **Note:** The full `requirements.txt` at the project root lists all team
> dependencies (voice, RAG, LLM, …). Install `backend/requirements.txt`
> instead to run only the FastAPI backend without heavy ML libraries.

### 3. Configure environment (optional for this milestone)

```bash
cp .env.example .env
# Edit .env to add API keys when integrating AI Core / Voice modules.
```

### 4. Run the backend

```bash
uvicorn backend.main:app --reload
```

The server starts at **http://localhost:8000**

### 5. Access API documentation

| Interface | URL |
|-----------|-----|
| Swagger UI (interactive) | http://localhost:8000/docs |
| ReDoc | http://localhost:8000/redoc |
| OpenAPI schema (JSON) | http://localhost:8000/openapi.json |

### 6. Sample requests

**Root check**
```bash
curl http://localhost:8000/
```

**Health check**
```bash
curl http://localhost:8000/health
```

**Ask the tutor a question**
```bash
curl -X POST http://localhost:8000/v1/ask \
  -H "Content-Type: application/json" \
  -d '{
    "question": "ما هو الحاسوب؟",
    "grade": "3",
    "subject": "cs",
    "language": "ar",
    "input_mode": "text",
    "mode": "explain"
  }'
```

Expected response shape:
```json
{
  "status": "success",
  "answer": "[EXPLAIN] هذا شرح تجريبي للسؤال الذي طرحته...",
  "spoken_answer": null,
  "sources": [
    {
      "book": "كتاب cs للصف 3",
      "lesson": "الوحدة الأولى",
      "page": 1,
      "chunk_id": "mock-chunk-001"
    }
  ],
  "confidence": null,
  "latency_ms": 0.02
}
```

### 7. Run the backend tests

```bash
# From the project root (no pytest needed – uses stdlib unittest)
python -m unittest tests.test_backend -v
```
