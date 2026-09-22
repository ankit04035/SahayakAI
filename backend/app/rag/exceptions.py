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


# ==============================================================================
# RAG PIPELINE & RETRIEVAL EXCEPTIONS (Step 7)
# ==============================================================================

class RAGError(AppException):
    """Base exception for all RAG retrieval and synthesis operations."""

    def __init__(
        self,
        message: str,
        status_code: int = 500,
        error_code: str = "RAG_ERROR",
        details: Optional[Any] = None,
    ):
        super().__init__(
            message=message,
            status_code=status_code,
            error_code=error_code,
            details=details,
        )


class DocumentNotFoundError(RAGError):
    """Raised when the target document for RAG querying does not exist."""

    def __init__(
        self,
        document_id: int,
        details: Optional[Any] = None,
    ):
        super().__init__(
            message=f"Document with ID {document_id} was not found.",
            status_code=404,
            error_code="DOCUMENT_NOT_FOUND",
            details=details,
        )


class DocumentNotProcessedError(RAGError):
    """Raised when querying a document whose processing status is not completed."""

    def __init__(
        self,
        document_id: int,
        status: str,
        details: Optional[Any] = None,
    ):
        super().__init__(
            message=f"Document {document_id} is not ready for retrieval (status: '{status}').",
            status_code=400,
            error_code="DOCUMENT_NOT_PROCESSED",
            details=details,
        )


class DocumentNoChunksError(RAGError):
    """Raised when a document has completed processing but contains no chunks."""

    def __init__(
        self,
        document_id: int,
        details: Optional[Any] = None,
    ):
        super().__init__(
            message=f"Document {document_id} has no chunks available for retrieval.",
            status_code=400,
            error_code="DOCUMENT_NO_CHUNKS",
            details=details,
        )


class DocumentNoEmbeddingsError(RAGError):
    """Raised when document chunks have not been embedded yet."""

    def __init__(
        self,
        document_id: int,
        details: Optional[Any] = None,
    ):
        super().__init__(
            message=f"Document {document_id} chunks do not have embeddings. Please compute embeddings before querying.",
            status_code=422,
            error_code="DOCUMENT_NO_EMBEDDINGS",
            details=details,
        )


class RAGQueryValidationError(RAGError):
    """Raised when a RAG question or parameters fail validation."""

    def __init__(
        self,
        message: str,
        details: Optional[Any] = None,
    ):
        super().__init__(
            message=message,
            status_code=400,
            error_code="RAG_QUERY_VALIDATION_ERROR",
            details=details,
        )


class SimilarityCalculationError(RAGError):
    """Raised when an error occurs during vector similarity computation."""

    def __init__(
        self,
        message: str = "Vector similarity computation failed.",
        details: Optional[Any] = None,
    ):
        super().__init__(
            message=message,
            status_code=500,
            error_code="SIMILARITY_CALCULATION_ERROR",
            details=details,
        )


class ContextBuildingError(RAGError):
    """Raised when building RAG context fails."""

    def __init__(
        self,
        message: str = "Failed to construct context for RAG query.",
        details: Optional[Any] = None,
    ):
        super().__init__(
            message=message,
            status_code=500,
            error_code="CONTEXT_BUILDING_ERROR",
            details=details,
        )

