"""
Embedding and Transformer Domain Exceptions.
Provides controlled application-level errors for model loading, validation,
generation, and persistence.
"""

from typing import Any, Optional
from backend.app.exceptions import AppException


class EmbeddingError(AppException):
    """Base exception for all embedding and transformer operations."""

    def __init__(
        self,
        message: str,
        status_code: int = 500,
        error_code: str = "EMBEDDING_ERROR",
        details: Optional[Any] = None,
    ):
        super().__init__(
            message=message,
            status_code=status_code,
            error_code=error_code,
            details=details,
        )


class EmbeddingModelLoadError(EmbeddingError):
    """Raised when the sentence transformer model fails to load or download."""

    def __init__(
        self,
        message: str = "Failed to load sentence transformer embedding model.",
        details: Optional[Any] = None,
    ):
        super().__init__(
            message=message,
            status_code=503,
            error_code="EMBEDDING_MODEL_LOAD_ERROR",
            details=details,
        )


class EmbeddingValidationError(EmbeddingError):
    """Raised when an embedding vector fails dimension or numerical validation."""

    def __init__(
        self,
        message: str = "Embedding vector validation failed.",
        details: Optional[Any] = None,
    ):
        super().__init__(
            message=message,
            status_code=400,
            error_code="EMBEDDING_VALIDATION_ERROR",
            details=details,
        )


class EmbeddingGenerationError(EmbeddingError):
    """Raised when an error occurs during embedding vector inference."""

    def __init__(
        self,
        message: str = "Failed to generate text embeddings.",
        details: Optional[Any] = None,
    ):
        super().__init__(
            message=message,
            status_code=500,
            error_code="EMBEDDING_GENERATION_ERROR",
            details=details,
        )


class EmbeddingPersistenceError(EmbeddingError):
    """Raised when persisting embeddings into database fails."""

    def __init__(
        self,
        message: str = "Failed to persist document chunk embeddings to database.",
        details: Optional[Any] = None,
    ):
        super().__init__(
            message=message,
            status_code=500,
            error_code="EMBEDDING_PERSISTENCE_ERROR",
            details=details,
        )
