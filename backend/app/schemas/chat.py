"""
ChatSession and ChatMessage Pydantic Schemas.
Defines validation and serialization models for conversational chat interactions,
session management, and document-grounded responses.
"""

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional, Union
from pydantic import BaseModel, ConfigDict, Field, field_validator
from backend.app.schemas.common import TimestampSchema
from backend.app.schemas.rag import SourceReferenceSchema


class ChatMessageBase(BaseModel):
    """Base message fields."""

    role: Literal["user", "assistant", "system"] = Field(..., description="Message author role")
    content: str = Field(..., min_length=1, max_length=20000, description="Message body text")
    source_metadata: Optional[Union[List[Dict[str, Any]], Dict[str, Any]]] = Field(
        None, description="Context citation references and grounding metadata"
    )


class ChatMessageCreate(ChatMessageBase):
    """Payload for creating a chat message."""

    session_id: int


class ChatMessageRead(ChatMessageBase):
    """Public message response schema."""

    id: int
    session_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ChatSessionBase(BaseModel):
    """Base session fields."""

    title: str = Field(default="New Chat", min_length=1, max_length=255, description="Human-readable session title")
    document_id: Optional[int] = Field(None, description="Optional associated document ID for RAG grounding")


class ChatSessionCreate(BaseModel):
    """Payload for creating a chat session."""

    title: Optional[str] = Field(default="New Chat", max_length=255, description="Optional custom session title")
    document_id: Optional[int] = Field(None, description="Optional document ID to associate with session")
    user_id: Optional[int] = Field(None, description="Optional user ID; defaults to active dev user if omitted")

    @field_validator("title")
    @classmethod
    def validate_title(cls, v: Optional[str]) -> str:
        if v is not None:
            cleaned = v.strip()
            if cleaned:
                return cleaned[:255]
        return "New Chat"


class ChatSessionUpdate(BaseModel):
    """Payload for updating session metadata."""

    title: str = Field(..., min_length=1, max_length=255, description="Updated session title")

    @field_validator("title")
    @classmethod
    def validate_title(cls, v: str) -> str:
        cleaned = v.strip()
        if not cleaned:
            raise ValueError("Title cannot be empty or contain only whitespace.")
        return cleaned[:255]


class ChatSessionRead(ChatSessionBase, TimestampSchema):
    """Public session response schema."""

    id: int
    user_id: int

    model_config = ConfigDict(from_attributes=True)


class ChatRequest(BaseModel):
    """Payload for sending a user question to a chat session."""

    message: str = Field(
        ...,
        min_length=1,
        max_length=4000,
        description="The user question or study prompt.",
        examples=["What is virtual memory and how does paging work?"],
    )
    top_k: Optional[int] = Field(
        default=None,
        gt=0,
        le=50,
        description="Optional override for maximum number of document chunks to retrieve.",
    )
    similarity_threshold: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Optional override for minimum cosine similarity threshold.",
    )

    @field_validator("message")
    @classmethod
    def validate_message(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Message cannot be empty or contain only whitespace.")
        return v.strip()


class ChatResponse(BaseModel):
    """Response returned when submitting a chat message."""

    session_id: int = Field(..., description="ID of the chat session")
    user_message: ChatMessageRead = Field(..., description="Persisted user message record")
    assistant_message: ChatMessageRead = Field(..., description="Persisted assistant response record")
    grounded: bool = Field(..., description="True if answer is directly derived from document evidence")
    insufficient_evidence: bool = Field(
        default=False,
        description="True if document lacked relevant evidence to answer the question",
    )
    sources: List[SourceReferenceSchema] = Field(
        default_factory=list,
        description="List of cited source chunks used as reference evidence",
    )
    provider: str = Field(..., description="AI provider used for synthesis (e.g. demo, openai, gemini)")
    model: str = Field(..., description="Model identifier used for generation")
