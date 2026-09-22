"""
Document Chunk Semantic Retrieval Engine.
Loads candidate chunk embeddings from the SQLite database, computes cosine similarity
against the query embedding, applies threshold filtering, and enforces deterministic top-K ranking.
"""

import logging
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session

from backend.app.config import get_settings
from backend.app.models.document import Document, DocumentChunk
from backend.app.rag.embedding_service import embed_query
from backend.app.rag.exceptions import (
    DocumentNoChunksError,
    DocumentNoEmbeddingsError,
    DocumentNotFoundError,
    DocumentNotProcessedError,
    EmbeddingValidationError,
)
from backend.app.rag.models import RetrievedChunk
from backend.app.rag.similarity import cosine_similarity
from backend.app.rag.vector_utils import deserialize_vector

logger = logging.getLogger("sahayakai.rag.retrieval")


def retrieve_chunks(
    document_id: int,
    query: str,
    db: Session,
    top_k: Optional[int] = None,
    similarity_threshold: Optional[float] = None,
) -> Tuple[List[RetrievedChunk], bool, int]:
    """
    Retrieve semantically relevant chunks for a given query scoped to a single document.

    Args:
        document_id: ID of the document to query.
        query: Raw user question/query string.
        db: Active SQLAlchemy database session.
        top_k: Maximum number of chunks to return (defaults to settings.RAG_TOP_K).
        similarity_threshold: Minimum cosine similarity score (defaults to settings.RAG_SIMILARITY_THRESHOLD).

    Returns:
        Tuple of:
            - List of selected RetrievedChunk objects ranked by relevance.
            - Boolean flag indicating whether sufficient evidence was found (best match >= threshold).
            - Total count of scored chunks for this document.

    Raises:
        DocumentNotFoundError: If document_id does not exist.
        DocumentNotProcessedError: If document processing status is not 'completed'.
        DocumentNoChunksError: If document contains no chunks.
        DocumentNoEmbeddingsError: If chunks do not have computed embeddings.
    """
    settings = get_settings()
    effective_top_k = top_k if (top_k is not None and top_k > 0) else settings.RAG_TOP_K
    effective_threshold = (
        similarity_threshold
        if (similarity_threshold is not None and 0.0 <= similarity_threshold <= 1.0)
        else settings.RAG_SIMILARITY_THRESHOLD
    )

    # 1. Document Existence and State Validation
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise DocumentNotFoundError(document_id=document_id)

    if doc.processing_status != "completed":
        raise DocumentNotProcessedError(
            document_id=document_id,
            status=doc.processing_status,
        )

    # 2. Load Scoped Chunks
    chunks = (
        db.query(DocumentChunk)
        .filter(DocumentChunk.document_id == document_id)
        .order_by(DocumentChunk.chunk_index.asc())
        .all()
    )

    if not chunks:
        raise DocumentNoChunksError(document_id=document_id)

    # Check for embeddings presence
    valid_chunks: List[DocumentChunk] = []
    for c in chunks:
        if c.embedding is not None:
            valid_chunks.append(c)

    if not valid_chunks:
        raise DocumentNoEmbeddingsError(document_id=document_id)

    # 3. Generate Query Embedding
    query_vector = embed_query(query)

    # 4. Score Candidate Chunks
    candidates: List[RetrievedChunk] = []
    for chunk in valid_chunks:
        try:
            chunk_vector = deserialize_vector(chunk.embedding, expected_dim=settings.EMBEDDING_DIMENSION)
            sim = cosine_similarity(query_vector, chunk_vector, expected_dim=settings.EMBEDDING_DIMENSION)
        except EmbeddingValidationError as err:
            logger.warning(
                "Skipping corrupt vector for chunk_id=%d: %s",
                chunk.id,
                err,
            )
            continue

        # Extract page number if present in metadata
        page_num: Optional[int] = None
        if chunk.chunk_metadata and isinstance(chunk.chunk_metadata, dict):
            page_num = chunk.chunk_metadata.get("page") or chunk.chunk_metadata.get("page_number")
            if page_num is not None:
                try:
                    page_num = int(page_num)
                except (ValueError, TypeError):
                    page_num = None

        candidates.append(
            RetrievedChunk(
                chunk_id=chunk.id,
                document_id=chunk.document_id,
                chunk_index=chunk.chunk_index,
                content=chunk.content,
                similarity=sim,
                page=page_num,
                character_count=chunk.character_count,
            )
        )

    if not candidates:
        raise DocumentNoEmbeddingsError(
            document_id=document_id,
            details={"reason": "All chunk embeddings failed deserialization or validation."},
        )

    # 5. Deterministic Ranking: similarity descending, then chunk_index ascending
    candidates.sort(key=lambda c: (-c.similarity, c.chunk_index))

    # 6. Similarity Threshold Evaluation
    best_similarity = candidates[0].similarity if candidates else -1.0
    has_sufficient_evidence = best_similarity >= effective_threshold

    # Filter candidates meeting the similarity threshold
    filtered_candidates = [c for c in candidates if c.similarity >= effective_threshold]

    # 7. Top-K Selection
    selected_top_k = filtered_candidates[:effective_top_k]

    return selected_top_k, has_sufficient_evidence, len(candidates)
