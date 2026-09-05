"""Application configuration — loads API keys from .env file."""

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Settings loaded from environment variables / .env file."""

    # LLM
    ANTHROPIC_API_KEY: str = ""

    # Weather
    OPENWEATHER_API_KEY: str = ""

    # Hotels & Activities use OpenStreetMap (Nominatim + Overpass) — no API key needed

    # Server
    BACKEND_CORS_ORIGINS: list[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
    ]

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


@lru_cache
def get_settings() -> Settings:
    """Cached settings instance — reads .env once."""
    return Settings()
