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
    AUTH_REQUIRED: bool = Field(default=True, description="Require authenticated sessions for application APIs")
    AUTH_COOKIE_SECURE: bool = Field(default=False, description="Mark authentication cookies Secure (enable for HTTPS)")
    AUTH_SESSION_DAYS: int = Field(default=30, gt=0, le=365, description="Browser session lifetime in days")

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
        default=["http://localhost:5173", "http://127.0.0.1:5173"],
        description="Allowed CORS origins list or comma-separated string",
    )

    # Storage & Upload limits
    MAX_UPLOAD_SIZE_MB: int = Field(
        default=10,
        gt=0,
        le=100,
        description="Maximum file upload size in megabytes",
    )
    UPLOAD_DIR: str = Field(
        default="./uploads",
        description="Base directory for uploaded documents and files",
    )

    # Document Chunking settings
    CHUNK_SIZE: int = Field(
        default=500,
        gt=50,
        le=10000,
        description="Target character chunk size for document splitting",
    )
    CHUNK_OVERLAP: int = Field(
        default=50,
        ge=0,
        le=2000,
        description="Overlap in characters between consecutive chunks",
    )

    # Embedding & Transformer settings (Step 6)
    EMBEDDING_MODEL: str = Field(
        default="all-MiniLM-L6-v2",
        description="SentenceTransformer model name for text embeddings",
    )
    EMBEDDING_DIMENSION: int = Field(
        default=384,
        gt=0,
        le=4096,
        description="Expected embedding dimensionality for the configured model",
    )
    EMBEDDING_DEVICE: str = Field(
        default="cpu",
        description="Device for embedding inference (cpu or cuda)",
    )
    EMBEDDING_BATCH_SIZE: int = Field(
        default=32,
        gt=0,
        le=512,
        description="Batch size for generating embeddings",
    )
    EMBEDDING_NORMALIZE: bool = Field(
        default=True,
        description="Whether to L2-normalize embeddings for cosine similarity retrieval",
    )
    EMBEDDING_CACHE_DIR: Union[str, None] = Field(
        default=None,
        description="Optional local directory for caching transformer model weights",
    )

    # Vector Retrieval and RAG Settings (Step 7)
    RAG_TOP_K: int = Field(
        default=5,
        gt=0,
        le=50,
        description="Default number of top chunks to retrieve for RAG",
    )
    RAG_SIMILARITY_THRESHOLD: float = Field(
        default=0.35,
        ge=0.0,
        le=1.0,
        description="Minimum cosine similarity threshold for retrieved chunks",
    )
    RAG_MAX_CONTEXT_CHARS: int = Field(
        default=12000,
        gt=100,
        le=100000,
        description="Maximum total characters of retrieved context passed to LLM",
    )
    RAG_MAX_QUESTION_CHARS: int = Field(
        default=2000,
        gt=0,
        le=10000,
        description="Maximum question character length",
    )

    # Chat and Study Assistant Settings (Step 8)
    CHAT_MAX_MESSAGE_CHARS: int = Field(
        default=4000,
        gt=0,
        le=20000,
        description="Maximum character length for a single chat message",
    )
    CHAT_HISTORY_MAX_MESSAGES: int = Field(
        default=10,
        gt=0,
        le=50,
        description="Maximum number of previous messages included in prompt history",
    )
    CHAT_MAX_HISTORY_CHARS: int = Field(
        default=6000,
        gt=100,
        le=50000,
        description="Maximum cumulative characters of prior conversation history in prompt",
    )
    CHAT_MAX_TITLE_CHARS: int = Field(
        default=255,
        gt=0,
        le=255,
        description="Maximum character length for chat session title",
    )

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def assemble_database_url(cls, v: str) -> str:
        if isinstance(v, str) and v.startswith("postgres://"):
            return v.replace("postgres://", "postgresql://", 1)
        return v

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
        return ["http://localhost:5173", "http://127.0.0.1:5173"]

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
