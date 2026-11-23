"""
Wusool AI Tutor – FastAPI application entry-point.

Run with:
    uvicorn backend.main:app --reload

Swagger UI: http://localhost:8000/docs
ReDoc:      http://localhost:8000/redoc
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.api.ask_routes import router as ask_router
from backend.app.core.config import settings

# ---------------------------------------------------------------------------
# Application factory
# ---------------------------------------------------------------------------

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=settings.app_description,
    contact={
        "name": "Wusool Engineering Team",
    },
    license_info={
        "name": "MIT",
    },
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# ---------------------------------------------------------------------------
# Middleware
# ---------------------------------------------------------------------------

# Allow the React frontend (and Swagger UI) to reach the API during development.
# Tighten origins in production.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------

app.include_router(ask_router, prefix="/v1", tags=["Tutor"])

# ---------------------------------------------------------------------------
# Root & health endpoints
# ---------------------------------------------------------------------------


@app.get(
    "/",
    tags=["System"],
    summary="API root",
    description="Returns basic API identification information.",
)
def root() -> dict:
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "status": "running",
        "docs": "/docs",
    }


@app.get(
    "/health",
    tags=["System"],
    summary="Health check",
    description="Returns the operational health of the backend service.",
)
def health() -> dict:
    return {
        "status": "ok",
        "environment": settings.environment,
    }
