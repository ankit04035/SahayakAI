"""
Document and DocumentChunk Model Definitions.
Represents uploaded reference documents and vectorized text chunks for RAG.
"""

from sqlalchemy import Column, Integer, String, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from backend.app.database import Base
from backend.app.models.base import TimestampMixin, UTCDateTime, utc_now


class Document(Base, TimestampMixin):
    """Document entity representing an uploaded user document or knowledge base resource."""

    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title = Column(String(255), nullable=True)
    original_filename = Column(String(255), nullable=False)
    stored_filename = Column(String(255), nullable=False)
    file_type = Column(String(50), nullable=False)
    file_size = Column(Integer, nullable=False)
    mime_type = Column(String(100), nullable=True)
    extracted_text = Column(Text, nullable=True)
    processing_status = Column(String(50), nullable=False, default="pending")

    # Relationships
    user = relationship("User", back_populates="documents")
    chunks = relationship(
        "DocumentChunk",
        back_populates="document",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="DocumentChunk.chunk_index",
    )
    chat_sessions = relationship(
        "ChatSession",
        back_populates="document",
        foreign_keys="ChatSession.document_id",
    )

    def __repr__(self) -> str:
        return f"<Document(id={self.id}, user_id={self.user_id}, filename='{self.original_filename}', status='{self.processing_status}')>"


class DocumentChunk(Base):
    """Text segment extracted from a document with embedding representation for RAG retrieval."""

    __tablename__ = "document_chunks"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    document_id = Column(
        Integer,
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    chunk_index = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    character_count = Column(Integer, nullable=False)
    embedding = Column(JSON, nullable=True)  # Stored as JSON list of floats [0.123, -0.456, ...]
    chunk_metadata = Column(JSON, nullable=True)
    created_at = Column(UTCDateTime, default=utc_now, nullable=False)

    # Relationships
    document = relationship("Document", back_populates="chunks")

    def __repr__(self) -> str:
        return f"<DocumentChunk(id={self.id}, document_id={self.document_id}, index={self.chunk_index}, chars={self.character_count})>"
