"""Application settings via Pydantic v2 BaseSettings.

Values are read from environment variables (or a .env file when present).
All fields have sensible defaults so the app starts without configuration
in development; override per-environment in CI/CD.
"""

from pydantic import Field, PostgresDsn, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Top-level application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ------------------------------------------------------------------
    # Database
    # ------------------------------------------------------------------
    database_url: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/agentarmy",
        description="Async-compatible PostgreSQL URL (asyncpg driver required).",
    )
    db_pool_size: int = Field(default=10, ge=1, le=100)
    db_max_overflow: int = Field(default=20, ge=0, le=100)
    db_echo: bool = Field(default=False, description="Log all SQL statements.")

    # ------------------------------------------------------------------
    # API
    # ------------------------------------------------------------------
    api_title: str = "AgentArmy API"
    api_version: str = "1.0.0"
    debug: bool = False


settings = Settings()
