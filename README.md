# Wusool AI Tutor

An accessibility-first Arabic voice tutor for Grade 3 learners with dyslexia or visual impairment. The MVP combines a curriculum-grounded retrieval layer with browser speech input/output and an adaptive interface.

## MVP journey

1. A parent or teacher chooses the learner's accessibility mode.
2. The learner chooses Math or ICT by voice or by pressing a large card.
3. The tutor retrieves a lesson from the approved curriculum content.
4. The lesson is explained in simple Modern Standard Arabic and read aloud.
5. The tutor asks a spoken question, listens to the answer, and gives supportive feedback.

## Accessibility modes

- **Dyslexia:** calm colors, large spacing, short lines, and reduced visual density.
- **Visual impairment:** screen-reader landmarks, keyboard navigation, high contrast, large controls, and voice-first operation. The design does not assume that every visually impaired learner has zero usable vision.

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r backend/requirements.txt
uvicorn backend.app.main:app --reload
```

Open `http://127.0.0.1:8000`.

## Curriculum data

The uploaded Grade 3 Math PDF is image-based and must pass Arabic OCR plus human review before ingestion. Do not commit copyrighted textbooks or children's personal data to this public repository. Place authorized source files under `data/raw/` locally, then follow [the content pipeline](docs/CONTENT_PIPELINE.md).

## Current scope

This first slice includes the complete accessible learning loop and a small reviewed demo knowledge base. Production speech services, authenticated teacher dashboards, persistent progress, and group sessions are planned next.

