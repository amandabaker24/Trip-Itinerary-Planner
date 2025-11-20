"""Application configuration and settings."""

from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Defines runtime configuration values."""

    database_url: str = "sqlite:///./trip_planner.db"
    secret_key: str = "change-me-in-production"
    access_token_expire_minutes: int = 60 * 24

    model_config = SettingsConfigDict(env_prefix="TRIP_PLANNER_", case_sensitive=False)


@lru_cache
def get_settings() -> Settings:
    """Return cached settings instance to avoid re-parsing env vars."""
    return Settings()
