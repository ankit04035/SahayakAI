"""
Pydantic Schemas for Retrieval-Augmented Generation (RAG) and Document Q&A.
Defines request validation and response models for document question answering,
source citations, and chunk embedding operations.
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class RAGQueryRequest(BaseModel):
    """Payload for asking a question grounded in an uploaded document."""

    question: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="The question to be answered using the document's content.",
        examples=["What are the primary differences between arrays and linked lists?"],
    )
    top_k: Optional[int] = Field(
        default=None,
        gt=0,
        le=50,
        description="Optional override for maximum number of relevant chunks to retrieve.",
    )
    similarity_threshold: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Optional override for minimum cosine similarity threshold.",
    )


class SourceReferenceSchema(BaseModel):
    """Document chunk source reference indicating evidence citation."""

    chunk_id: int = Field(..., description="Unique database ID of the cited chunk")
    chunk_index: int = Field(..., description="0-based sequential index of the chunk in the document")
    page: Optional[int] = Field(None, description="Original 1-based page number where available")
    similarity: float = Field(..., description="Cosine similarity score against query embedding")


class RAGQueryResponse(BaseModel):
    """Response returned by document Q&A endpoint."""

    answer: str = Field(..., description="Grounded answer synthesized from document context")
    grounded: bool = Field(..., description="True if answer is directly derived from retrieved evidence")
    provider: str = Field(..., description="AI provider used for synthesis (e.g. demo, openai, gemini)")
    model: str = Field(..., description="Model identifier used for generation")
    sources: List[SourceReferenceSchema] = Field(
        default_factory=list,
        description="List of cited source chunks used as reference evidence",
    )
    query: str = Field(..., description="Normalized user query")
    retrieved_count: int = Field(..., description="Number of relevant chunks cited in the response")
    insufficient_evidence: bool = Field(
        default=False,
        description="True if query fell below similarity threshold and lacked sufficient evidence",
    )


class EmbedChunksResponse(BaseModel):
    """Response returned when triggering embedding computation for a document."""

    document_id: int = Field(..., description="Target document ID")
    embedded_chunks: int = Field(..., description="Number of chunks successfully embedded")
    status: str = Field(default="completed", description="Embedding operation status")
