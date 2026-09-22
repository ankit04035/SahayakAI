"""
RAG Context Construction and Context-Size Protection Engine.
Deduplicates retrieved chunks, enforces strict character budget limits, preserves source metadata,
and formats coherent reading context for generative AI synthesis.
"""

import hashlib
import logging
from typing import List, Optional, Set

from backend.app.config import get_settings
from backend.app.rag.models import RAGContext, RetrievedChunk, SourceReference

logger = logging.getLogger("sahayakai.rag.context_builder")


def build_rag_context(
    retrieved_chunks: List[RetrievedChunk],
    max_context_chars: Optional[int] = None,
) -> RAGContext:
    """
    Construct a bounded, deduplicated, and formatted context package from retrieved chunks.

    Strategy:
        1. Deduplication: Filter out chunks with duplicate IDs or identical content.
        2. Relevance Selection: Evaluate chunks in order of relevance (highest similarity).
        3. Budget Enforcement: Accumulate content characters up to max_context_chars.
           If adding a chunk would exceed the limit, stop adding further chunks.
        4. Coherent Ordering: Sort the accepted chunks by chunk_index ascending so the
           language model receives natural textual flow.
        5. Source References: Produce external-safe SourceReference objects for client attribution.

    Args:
        retrieved_chunks: Ranked list of RetrievedChunk objects.
        max_context_chars: Character limit for context. Defaults to settings.RAG_MAX_CONTEXT_CHARS.

    Returns:
        RAGContext containing formatted string, chosen chunks, sources, and total length.
    """
    settings = get_settings()
    budget = max_context_chars if (max_context_chars is not None and max_context_chars > 0) else settings.RAG_MAX_CONTEXT_CHARS

    if not retrieved_chunks:
        return RAGContext(
            formatted_context="",
            selected_chunks=[],
            sources=[],
            total_characters=0,
        )

    seen_ids: Set[int] = set()
    seen_hashes: Set[str] = set()
    accepted_chunks: List[RetrievedChunk] = []
    current_char_count = 0

    for chunk in retrieved_chunks:
        # Deduplication check by chunk_id
        if chunk.chunk_id in seen_ids:
            continue

        # Content fingerprint deduplication (collapsing identical duplicate paragraphs)
        content_hash = hashlib.sha256(chunk.content.strip().encode("utf-8")).hexdigest()
        if content_hash in seen_hashes:
            continue

        chunk_len = len(chunk.content)
        separator_len = 50  # Allowance for delimiter headers and newlines

        # Enforce strict budget boundary without partial truncation
        if current_char_count + chunk_len + separator_len > budget:
            logger.info(
                "RAG context character limit reached (%d + %d > %d). Stopping chunk accumulation.",
                current_char_count,
                chunk_len,
                budget,
            )
            break

        seen_ids.add(chunk.chunk_id)
        seen_hashes.add(content_hash)
        accepted_chunks.append(chunk)
        current_char_count += chunk_len + separator_len

    # Sort accepted chunks by chunk_index for sequential reading continuity
    accepted_chunks.sort(key=lambda c: c.chunk_index)

    # Format context blocks
    formatted_blocks: List[str] = []
    sources: List[SourceReference] = []

    for c in accepted_chunks:
        page_info = f" (Page {c.page})" if c.page is not None else ""
        header = f"[Document Chunk {c.chunk_index}{page_info}]"
        block = f"{header}\n{c.content.strip()}"
        formatted_blocks.append(block)
        sources.append(c.to_source_reference())

    full_context_text = "\n\n".join(formatted_blocks).strip()

    return RAGContext(
        formatted_context=full_context_text,
        selected_chunks=accepted_chunks,
        sources=sources,
        total_characters=len(full_context_text),
    )
