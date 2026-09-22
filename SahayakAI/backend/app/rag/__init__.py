"""
Retrieval-Augmented Generation (RAG) and Vector Embedding Package.
Provides end-to-end vector embeddings, semantic retrieval, context construction,
prompt assembly, and grounded question-answering over documents.
"""

from backend.app.rag.exceptions import (
    ContextBuildingError,
    DocumentNoChunksError,
    DocumentNoEmbeddingsError,
    DocumentNotFoundError,
    DocumentNotProcessedError,
    EmbeddingError,
    EmbeddingGenerationError,
    EmbeddingModelLoadError,
    EmbeddingPersistenceError,
    EmbeddingValidationError,
    RAGError,
    RAGQueryValidationError,
    SimilarityCalculationError,
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
from backend.app.rag.models import (
    RAGContext,
    RAGResult,
    RetrievedChunk,
    SourceReference,
)
from backend.app.rag.similarity import (
    compute_chunk_similarities,
    cosine_similarity,
)
from backend.app.rag.retrieval import retrieve_chunks
from backend.app.rag.context_builder import build_rag_context
from backend.app.rag.prompt_builder import build_rag_prompts
from backend.app.rag.rag_service import query_document

__all__ = [
    # Embedding exceptions
    "EmbeddingError",
    "EmbeddingGenerationError",
    "EmbeddingModelLoadError",
    "EmbeddingPersistenceError",
    "EmbeddingValidationError",
    # RAG exceptions
    "RAGError",
    "DocumentNotFoundError",
    "DocumentNotProcessedError",
    "DocumentNoChunksError",
    "DocumentNoEmbeddingsError",
    "RAGQueryValidationError",
    "SimilarityCalculationError",
    "ContextBuildingError",
    # Model manager & vector utilities
    "EmbeddingModelManager",
    "get_model_manager",
    "deserialize_vector",
    "serialize_vector",
    "validate_vector",
    # Embedding service
    "embed_batch",
    "embed_document_chunks",
    "embed_query",
    "embed_text",
    "get_embedding_dimension",
    # RAG models
    "RetrievedChunk",
    "SourceReference",
    "RAGContext",
    "RAGResult",
    # Similarity, Retrieval, Context, Prompt, Service
    "cosine_similarity",
    "compute_chunk_similarities",
    "retrieve_chunks",
    "build_rag_context",
    "build_rag_prompts",
    "query_document",
]
