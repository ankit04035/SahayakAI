"""
Retrieval-Augmented Generation (RAG) and Vector Embedding Package.
"""

from backend.app.rag.exceptions import (
    EmbeddingError,
    EmbeddingGenerationError,
    EmbeddingModelLoadError,
    EmbeddingPersistenceError,
    EmbeddingValidationError,
)
from backend.app.rag.model_manager import (
    EmbeddingModelManager,
    get_model_manager,
)
from backend.app.rag.vector_utils import (
    deserialize_vector,
    serialize_vector,
    validate_vector,
)
from backend.app.rag.embedding_service import (
    embed_batch,
    embed_document_chunks,
    embed_query,
    embed_text,
    get_embedding_dimension,
)

__all__ = [
    "EmbeddingError",
    "EmbeddingGenerationError",
    "EmbeddingModelLoadError",
    "EmbeddingPersistenceError",
    "EmbeddingValidationError",
    "EmbeddingModelManager",
    "get_model_manager",
    "deserialize_vector",
    "serialize_vector",
    "validate_vector",
    "embed_batch",
    "embed_document_chunks",
    "embed_query",
    "embed_text",
    "get_embedding_dimension",
]
