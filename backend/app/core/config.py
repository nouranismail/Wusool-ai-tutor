"""
Shared application configuration loaded from environment variables.

Other modules should import settings from here rather than reading
os.environ directly, so configuration stays centralised.
"""

import os


class Settings:
    """Lightweight settings container.  No external library required."""

    # Application identity
    app_name: str = "Wusool AI Tutor"
    app_version: str = "0.1.0"
    app_description: str = (
        "Voice-first AI educational tutor for children, "
        "including blind and visually impaired students."
    )

    # Server
    environment: str = os.getenv("ENVIRONMENT", "development")
    port: int = int(os.getenv("PORT", "8000"))

    # Future integration placeholders (not used in this milestone)
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    groq_api_key: str = os.getenv("GROQ_API_KEY", "")
    elevenlabs_api_key: str = os.getenv("ELEVENLABS_API_KEY", "")


settings = Settings()
