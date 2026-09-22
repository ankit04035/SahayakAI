"""
Document and DocumentChunk Pydantic Schemas.
Defines validation and serialization models for documents and vectorized chunks.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field
from backend.app.schemas.common import TimestampSchema


class DocumentBase(BaseModel):
    """Base document fields."""

    title: Optional[str] = Field(None, max_length=255)
    original_filename: str = Field(..., min_length=1, max_length=255)
    file_type: str = Field(..., max_length=50)
    file_size: int = Field(..., ge=0)
    mime_type: Optional[str] = Field(None, max_length=100)


class DocumentCreate(DocumentBase):
    """Payload for creating a document record."""

    user_id: int
    stored_filename: str = Field(..., min_length=1, max_length=255)
    extracted_text: Optional[str] = None
    processing_status: str = Field(default="pending", max_length=50)


class DocumentUpdate(BaseModel):
    """Payload for updating document status or extracted content."""

    title: Optional[str] = None
    extracted_text: Optional[str] = None
    processing_status: Optional[str] = None


class DocumentRead(DocumentBase, TimestampSchema):
    """Public document response schema."""

    id: int
    user_id: int
    stored_filename: str
    extracted_text: Optional[str] = None
    processing_status: str

    model_config = ConfigDict(from_attributes=True)


class DocumentDetailRead(DocumentRead):
    """Detailed document response with chunk count and statistics."""

    chunk_count: int = 0
    character_count: int = 0
    word_count: int = 0
    page_count: int = 1
    primary_language: str = "unknown"
    keywords: List[Dict[str, Any]] = Field(default_factory=list)


class DocumentUploadResponse(BaseModel):
    """Structured response returned immediately upon successful document upload and processing."""

    id: int
    user_id: int
    title: Optional[str] = None
    original_filename: str
    stored_filename: str
    file_type: str
    file_size: int
    mime_type: Optional[str] = None
    processing_status: str
    character_count: int = Field(default=0, ge=0)
    word_count: int = Field(default=0, ge=0)
    page_count: int = Field(default=1, ge=1)
    chunk_count: int = Field(default=0, ge=0)
    primary_language: str = "unknown"
    keywords: List[Dict[str, Any]] = Field(default_factory=list)
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DocumentChunkBase(BaseModel):
    """Base chunk schema."""

    chunk_index: int = Field(..., ge=0)
    content: str = Field(..., min_length=1)
    character_count: int = Field(..., gt=0)


class DocumentChunkCreate(DocumentChunkBase):
    """Payload for creating a document chunk."""

    document_id: int
    embedding: Optional[List[float]] = None
    chunk_metadata: Optional[Dict[str, Any]] = None


class DocumentChunkRead(DocumentChunkBase):
    """Public document chunk response schema."""

    id: int
    document_id: int
    embedding: Optional[List[float]] = None
    chunk_metadata: Optional[Dict[str, Any]] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
