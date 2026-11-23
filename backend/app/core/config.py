"""
Centralised application settings loaded from .env / environment variables.
Never read os.environ directly in other modules — import `settings` from here.
"""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

# Load .env from the backend directory (two levels up from this file)
_env_path = Path(__file__).resolve().parents[3] / ".env"
load_dotenv(dotenv_path=_env_path)


class Settings:
    # App identity
    app_name: str = "Wusool AI Tutor"
    app_version: str = "0.2.0"
    app_description: str = (
        "Voice-first AI educational tutor for children, "
        "including blind and visually impaired students."
    )

    # Server
    environment: str = os.getenv("ENVIRONMENT", "development")
    port: int = int(os.getenv("PORT", "8000"))
    frontend_origin: str = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")

    # Database
    database_url: str = os.getenv(
        "DATABASE_URL",
        "postgresql://wusool:wusool@localhost:5432/wusool_db",
    )

    # JWT
    jwt_secret_key: str = os.getenv("JWT_SECRET_KEY", "CHANGE-ME")
    jwt_algorithm: str = os.getenv("JWT_ALGORITHM", "HS256")
    access_token_expire_minutes: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))

    # Admin static token (for RAG upload endpoint)
    admin_token: str = os.getenv("ADMIN_TOKEN", "CHANGE-ME")

    # Supported values — must match what the frontend offers
    supported_grades: list[int] = [3, 4]
    supported_subjects: list[str] = ["english", "ict"]
    supported_languages: list[str] = ["ar", "en"]


settings = Settings()
