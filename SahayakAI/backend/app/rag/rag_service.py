"""
Retrieval-Augmented Generation (RAG) Service Coordinator.
Orchestrates query validation, candidate vector retrieval, threshold evaluation,
context construction, prompt assembly, and AI provider synthesis.
"""

import logging
from typing import Optional
from sqlalchemy.orm import Session

from backend.app.config import get_settings
from backend.app.providers import get_provider
from backend.app.rag.context_builder import build_rag_context
from backend.app.rag.exceptions import RAGQueryValidationError
from backend.app.rag.models import RAGResult
from backend.app.rag.prompt_builder import build_rag_prompts
from backend.app.rag.retrieval import retrieve_chunks

logger = logging.getLogger("sahayakai.rag.service")


def query_document(
    document_id: int,
    question: str,
    db: Session,
    top_k: Optional[int] = None,
    similarity_threshold: Optional[float] = None,
) -> RAGResult:
    """
    Execute end-to-end document-grounded question answering.

    Flow:
        1. Validate query constraints (non-empty, length bounds).
        2. Retrieve candidate chunks and evaluate similarity scores against threshold.
        3. If evidence is insufficient, return controlled response without calling LLM.
        4. Assemble bounded, deduplicated context.
        5. Construct provider-neutral grounded prompt with injection guardrails.
        6. Invoke active AI provider (Demo, OpenAI, Gemini).
        7. Return structured RAGResult with source citations.

    Args:
        document_id: ID of target document.
        question: User query string.
        db: SQLAlchemy session.
        top_k: Optional top-K chunk retrieval override.
        similarity_threshold: Optional similarity threshold override.

    Returns:
        RAGResult containing synthesized answer, grounding status, source citations, and metadata.
    """
    settings = get_settings()

    # 1. Query Validation
    if not question or not question.strip():
        raise RAGQueryValidationError("Question cannot be empty or contain only whitespace.")

    cleaned_question = question.strip()
    if len(cleaned_question) > settings.RAG_MAX_QUESTION_CHARS:
        raise RAGQueryValidationError(
            f"Question length ({len(cleaned_question)}) exceeds maximum limit of {settings.RAG_MAX_QUESTION_CHARS} characters."
        )

    # 2. Retrieve Candidate Chunks & Check Evidence
    selected_chunks, has_sufficient_evidence, scored_count = retrieve_chunks(
        document_id=document_id,
        query=cleaned_question,
        db=db,
        top_k=top_k,
        similarity_threshold=similarity_threshold,
    )

    provider = get_provider()

    # 3. Insufficient Evidence Handling: Do NOT call LLM with unrelated context
    if not has_sufficient_evidence or not selected_chunks:
        logger.info(
            "Query on document_id=%d yielded insufficient evidence (scored %d chunks). Returning controlled response.",
            document_id,
            scored_count,
        )
        return RAGResult(
            answer=(
                "The provided document does not contain sufficient relevant information "
                "to answer this question."
            ),
            grounded=False,
            provider=provider.provider_name,
            model=provider.default_model,
            sources=[],
            query=cleaned_question,
            retrieved_count=0,
            insufficient_evidence=True,
            metadata={
                "document_id": document_id,
                "scored_chunks": scored_count,
                "reason": "Similarity scores fell below minimum relevance threshold.",
            },
        )

    # 4. Context Assembly with Length Protection
    rag_context = build_rag_context(
        retrieved_chunks=selected_chunks,
        max_context_chars=settings.RAG_MAX_CONTEXT_CHARS,
    )

    # 5. Prompt Construction
    system_prompt, user_prompt = build_rag_prompts(
        context_text=rag_context.formatted_context,
        question=cleaned_question,
    )

    # 6. AI Provider Synthesis
    provider_response = provider.generate(
        prompt=user_prompt,
        system_prompt=system_prompt,
        temperature=settings.AI_TEMPERATURE,
        max_tokens=settings.AI_MAX_TOKENS,
    )

    # 7. Construct Final Response
    return RAGResult(
        answer=provider_response.generated_text,
        grounded=True,
        provider=provider_response.provider,
        model=provider_response.model,
        sources=rag_context.sources,
        query=cleaned_question,
        retrieved_count=len(rag_context.selected_chunks),
        insufficient_evidence=False,
        metadata={
            "document_id": document_id,
            "latency_ms": provider_response.latency_ms,
            "total_context_chars": rag_context.total_characters,
            "scored_chunks": scored_count,
        },
    )
