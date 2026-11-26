from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

ENV_FILE = Path(__file__).resolve().parents[2] / ".env"


class Settings(BaseSettings):
    """Configuración de entorno de CruciWord."""

    model_config = SettingsConfigDict(env_file=ENV_FILE, extra="ignore")

    DATABASE_URL: str = "sqlite:///./cruciword.db"
    SECRET_KEY: str = "dev-only-insecure-change-me-32chars!!"
    ALGORITHM: str = "HS256"


@lru_cache
def get_settings() -> Settings:
    """Devuelve la configuración cacheada del proceso."""
    return Settings()
