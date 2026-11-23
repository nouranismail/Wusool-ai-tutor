"""
Wusool AI Tutor — FastAPI application entry-point.

Run:
    uvicorn backend.main:app --reload

Swagger UI:  http://localhost:8000/docs
ReDoc:       http://localhost:8000/redoc
API base:    http://localhost:8000/api
WS base:     ws://localhost:8000/ws
"""
from __future__ import annotations
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.core.config import settings

# --- New /api routers ---
from backend.app.api.auth import router as auth_router
from backend.app.api.children import router as children_router
from backend.app.api.study import router as study_router
from backend.app.api.progress import router as progress_router
from backend.app.api.chat import router as chat_router
from backend.app.api.voice import router as voice_router
from backend.app.api.friends import router as friends_router
from backend.app.api.sessions import router as sessions_router
from backend.app.api.rag import router as rag_router

# --- WebSocket routers (/ws) ---
from backend.app.api.websockets import router as ws_router

# --- Legacy /v1 router (kept untouched) ---
from backend.app.api.ask_routes import router as ask_router

logger = logging.getLogger("wusool")

# ---------------------------------------------------------------------------
# Create DB tables on startup (dev convenience).
# Use Alembic migrations for production deployments.
# ---------------------------------------------------------------------------

def _create_tables() -> None:
    try:
        from backend.app.db.base import Base
        from backend.app.db import models as _models  # noqa: F401 — registers all ORM classes
        from backend.app.db.session import engine
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables verified / created.")
    except Exception as exc:
        logger.warning(f"Could not create DB tables (is PostgreSQL running?): {exc}")


_create_tables()

# ---------------------------------------------------------------------------
# Application factory
# ---------------------------------------------------------------------------

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=settings.app_description,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin, "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Register routers
# ---------------------------------------------------------------------------

app.include_router(auth_router,     prefix="/api", tags=["Auth"])
app.include_router(children_router, prefix="/api", tags=["Children"])
app.include_router(study_router,    prefix="/api", tags=["Study"])
app.include_router(progress_router, prefix="/api", tags=["Progress"])
app.include_router(chat_router,     prefix="/api", tags=["Chat"])
app.include_router(voice_router,    prefix="/api", tags=["Voice"])
app.include_router(friends_router,  prefix="/api", tags=["Friends"])
app.include_router(sessions_router, prefix="/api", tags=["Sessions"])
app.include_router(rag_router,      prefix="/api", tags=["RAG (Admin)"])

app.include_router(ws_router,       prefix="/ws",  tags=["WebSocket"])

# Legacy endpoint — preserved as-is
app.include_router(ask_router,      prefix="/v1",  tags=["Legacy v1"])


# ---------------------------------------------------------------------------
# System endpoints
# ---------------------------------------------------------------------------

@app.get("/", tags=["System"])
def root() -> dict:
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "status": "running",
        "docs": "/docs",
        "api_base": "/api",
        "ws_base": "/ws",
    }


@app.get("/health", tags=["System"])
def health() -> dict:
    return {"status": "ok", "environment": settings.environment}
