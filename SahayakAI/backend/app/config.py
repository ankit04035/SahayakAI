"""
Application Configuration Module.
Provides typed, validated settings loaded from environment variables and .env files.
"""

from functools import lru_cache
from typing import List, Union
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings schema with sensible defaults and environment loading."""

    APP_NAME: str = Field(default="SahayakAI", description="Application name")
    APP_VERSION: str = Field(default="0.1.0", description="Application semantic version")
    ENVIRONMENT: str = Field(default="development", description="Deployment environment")
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")

    # Database
    DATABASE_URL: str = Field(
        default="sqlite:///./data/sahayakai.db",
        description="SQLAlchemy database connection string",
    )

    # AI Provider settings
    AI_PROVIDER: str = Field(
        default="demo",
        description="Selected AI provider mode: demo, openai, gemini",
    )
    OPENAI_API_KEY: str | None = Field(
        default=None,
        description="OpenAI API key (optional, not required in demo mode)",
    )
    OPENAI_BASE_URL: str | None = Field(
        default=None,
        description="Optional base URL for OpenAI-compatible providers (Ollama, vLLM, Groq)",
    )
    OPENAI_MODEL: str = Field(
        default="gpt-4o-mini",
        description="Default model for OpenAI-compatible provider",
    )
    GEMINI_API_KEY: str | None = Field(
        default=None,
        description="Google Gemini API key (optional, not required in demo mode)",
    )
    GEMINI_MODEL: str = Field(
        default="gemini-1.5-flash",
        description="Default model for Gemini provider",
    )
    AI_TIMEOUT_SECONDS: int = Field(
        default=30,
        gt=0,
        le=300,
        description="Default timeout in seconds for AI provider calls",
    )
    AI_MAX_TOKENS: int = Field(
        default=1000,
        gt=0,
        le=32000,
        description="Default max tokens for generation",
    )
    AI_TEMPERATURE: float = Field(
        default=0.2,
        ge=0.0,
        le=2.0,
        description="Default sampling temperature for AI generation",
    )

    # CORS Settings
    CORS_ORIGINS: Union[List[str], str] = Field(
        default=["http://localhost:5173"],
        description="Allowed CORS origins list or comma-separated string",
    )

    # Storage & Upload limits
    MAX_UPLOAD_SIZE_MB: int = Field(
        default=10,
        gt=0,
        le=100,
        description="Maximum file upload size in megabytes",
    )

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            v = v.strip()
            if v.startswith("[") and v.endswith("]"):
                import json
                try:
                    parsed = json.loads(v)
                    if isinstance(parsed, list):
                        return [str(i).strip() for i in parsed if str(i).strip()]
                except Exception:
                    pass
            return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, (list, tuple)):
            return [str(i).strip() for i in v if str(i).strip()]
        return ["http://localhost:5173"]

    @field_validator("AI_PROVIDER", mode="before")
    @classmethod
    def validate_ai_provider(cls, v: str) -> str:
        if isinstance(v, str):
            val = v.lower().strip()
            if val:
                return val
        return "demo"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=True,
    )


@lru_cache
def get_settings() -> Settings:
    """Return cached Settings instance."""
    return Settings()
