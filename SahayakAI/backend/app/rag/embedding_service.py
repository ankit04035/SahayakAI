"""
Sentence Transformer Embedding Service.
Provides single-text, batch, query, and document-chunk embedding generation
using all-MiniLM-L6-v2 with strict dimension validation and database persistence.
"""

import logging
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session

from backend.app.config import get_settings
from backend.app.exceptions import AppException
from backend.app.models.document import Document, DocumentChunk
from backend.app.rag.exceptions import (
    EmbeddingGenerationError,
    EmbeddingPersistenceError,
    EmbeddingValidationError,
)
from backend.app.rag.model_manager import get_model_manager
from backend.app.rag.vector_utils import (
    deserialize_vector,
    serialize_vector,
    validate_vector,
)

logger = logging.getLogger("sahayakai.rag.embedding_service")


def get_embedding_dimension() -> int:
    """Return configured embedding dimension."""
    return get_settings().EMBEDDING_DIMENSION


def embed_text(text: str) -> List[float]:
    """
    Generate embedding for a single text string.
    L2-normalizes the output vector according to configuration.
    """
    if text is None or not isinstance(text, str) or not text.strip():
        raise EmbeddingValidationError("Text to embed cannot be empty or null.")

    settings = get_settings()
    model_manager = get_model_manager()
    model = model_manager.load_model()

    try:
        vector = model.encode(
            text.strip(),
            batch_size=1,
            show_progress_bar=False,
            normalize_embeddings=settings.EMBEDDING_NORMALIZE,
            convert_to_numpy=True,
        )
        return serialize_vector(vector, expected_dim=settings.EMBEDDING_DIMENSION)
    except Exception as exc:
        if isinstance(exc, AppException):
            raise exc
        logger.error("Failed to generate embedding: %s", exc, exc_info=True)
        raise EmbeddingGenerationError(f"Embedding generation failed: {str(exc)}")


def embed_batch(texts: List[str], batch_size: Optional[int] = None) -> List[List[float]]:
    """
    Generate embeddings for a collection of texts in configurable batch sizes.
    Returns empty list if texts list is empty.
    """
    if not texts:
        return []

    settings = get_settings()
    size = batch_size or settings.EMBEDDING_BATCH_SIZE
    model_manager = get_model_manager()
    model = model_manager.load_model()

    # Pre-validate texts
    clean_texts: List[str] = []
    for i, t in enumerate(texts):
        if t is None or not isinstance(t, str) or not t.strip():
            raise EmbeddingValidationError(f"Text at index {i} is empty or invalid.")
        clean_texts.append(t.strip())

    try:
        raw_vectors = model.encode(
            clean_texts,
            batch_size=size,
            show_progress_bar=False,
            normalize_embeddings=settings.EMBEDDING_NORMALIZE,
            convert_to_numpy=True,
        )

        embeddings: List[List[float]] = []
        for vec in raw_vectors:
            embeddings.append(serialize_vector(vec, expected_dim=settings.EMBEDDING_DIMENSION))

        return embeddings
    except Exception as exc:
        if isinstance(exc, AppException):
            raise exc
        logger.error("Failed to generate batch embeddings: %s", exc, exc_info=True)
        raise EmbeddingGenerationError(f"Batch embedding generation failed: {str(exc)}")


def embed_query(query: str) -> List[float]:
    """
    Generate an embedding for a user query.
    Preserves multilingual characters (English, Hindi, Hinglish) without destructive modification.
    Applies identical model and normalization as document chunk embeddings.
    """
    if query is None or not isinstance(query, str) or not query.strip():
        raise EmbeddingValidationError("Search query cannot be empty or whitespace.")

    return embed_text(query.strip())


def embed_document_chunks(
    document_id: int,
    db: Session,
    batch_size: Optional[int] = None,
) -> int:
    """
    Batch generate and persist embeddings for all chunks of a document.
    Transactionally safe: rolls back database session if any batch or vector fails.
    Returns the number of successfully embedded chunks.
    """
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise AppException(
            message=f"Document with ID {document_id} not found.",
            status_code=404,
            error_code="DOCUMENT_NOT_FOUND",
        )

    chunks = (
        db.query(DocumentChunk)
        .filter(DocumentChunk.document_id == document_id)
        .order_by(DocumentChunk.chunk_index.asc())
        .all()
    )

    if not chunks:
        logger.info("No chunks found for document %d; skipping embedding.", document_id)
        return 0

    chunk_texts = [c.content for c in chunks]

    try:
        vectors = embed_batch(chunk_texts, batch_size=batch_size)
        if len(vectors) != len(chunks):
            raise EmbeddingPersistenceError(
                f"Generated vector count ({len(vectors)}) does not match chunk count ({len(chunks)})."
            )

        for chunk, vec in zip(chunks, vectors):
            chunk.embedding = vec

        db.commit()
        for chunk in chunks:
            db.refresh(chunk)

        logger.info("Successfully generated and persisted %d embeddings for document %d.", len(chunks), document_id)
        return len(chunks)

    except Exception as exc:
        db.rollback()
        logger.error("Failed to embed document chunks for document %d: %s", document_id, exc, exc_info=True)
        if isinstance(exc, AppException):
            raise exc
        raise EmbeddingPersistenceError(
            message=f"Failed to persist embeddings for document {document_id}: {str(exc)}",
            details={"document_id": document_id, "error": str(exc)},
        )
