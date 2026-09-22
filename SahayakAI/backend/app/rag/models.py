"""
RAG Domain Internal Data Models.
Defines structured objects for retrieved chunks, source references,
assembled context, and RAG execution results.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class RetrievedChunk:
    """Represents a document chunk scored against a query embedding."""

    chunk_id: int
    document_id: int
    chunk_index: int
    content: str
    similarity: float
    page: Optional[int] = None
    character_count: int = 0

    def to_source_reference(self) -> "SourceReference":
        """Convert chunk metadata to a public source reference."""
        return SourceReference(
            chunk_id=self.chunk_id,
            chunk_index=self.chunk_index,
            page=self.page,
            similarity=round(self.similarity, 4),
        )


@dataclass
class SourceReference:
    """Document chunk source attribution for external API responses."""

    chunk_id: int
    chunk_index: int
    similarity: float
    page: Optional[int] = None


@dataclass
class RAGContext:
    """Assembled and bounded context package prepared for prompt construction."""

    formatted_context: str
    selected_chunks: List[RetrievedChunk] = field(default_factory=list)
    sources: List[SourceReference] = field(default_factory=list)
    total_characters: int = 0


@dataclass
class RAGResult:
    """Complete result of a RAG query execution."""

    answer: str
    grounded: bool
    provider: str
    model: str
    sources: List[SourceReference] = field(default_factory=list)
    query: str = ""
    retrieved_count: int = 0
    insufficient_evidence: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)
