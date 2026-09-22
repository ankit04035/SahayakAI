"""
ChatSession and ChatMessage Pydantic Schemas.
Defines validation and serialization models for conversational chat interactions.
"""

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional, Union
from pydantic import BaseModel, ConfigDict, Field
from backend.app.schemas.common import TimestampSchema


class ChatMessageBase(BaseModel):
    """Base message fields."""

    role: Literal["user", "assistant", "system"] = Field(..., description="Message author role")
    content: str = Field(..., min_length=1, description="Message body text")
    source_metadata: Optional[Union[List[Dict[str, Any]], Dict[str, Any]]] = Field(
        None, description="Context citation references"
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

    title: str = Field(default="New Chat", min_length=1, max_length=255)
    document_id: Optional[int] = None


class ChatSessionCreate(ChatSessionBase):
    """Payload for creating a chat session."""

    user_id: int


class ChatSessionRead(ChatSessionBase, TimestampSchema):
    """Public session response schema."""

    id: int
    user_id: int

    model_config = ConfigDict(from_attributes=True)
