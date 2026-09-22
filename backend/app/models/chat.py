"""
ChatSession and ChatMessage Model Definitions.
Represents conversational interactions and citation sources between user and SahayakAI.
"""

from sqlalchemy import Column, Integer, String, Text, ForeignKey, JSON, CheckConstraint, DateTime
from sqlalchemy.orm import relationship
from backend.app.database import Base
from backend.app.models.base import TimestampMixin, UTCDateTime, utc_now


class ChatSession(Base, TimestampMixin):
    """Chat session container grouping ordered conversational messages."""

    __tablename__ = "chat_sessions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    document_id = Column(
        Integer,
        ForeignKey("documents.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    title = Column(String(255), nullable=False, default="New Chat")

    # Relationships
    user = relationship("User", back_populates="chat_sessions")
    document = relationship("Document", back_populates="chat_sessions")
    messages = relationship(
        "ChatMessage",
        back_populates="session",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="ChatMessage.id",
    )

    def __repr__(self) -> str:
        return f"<ChatSession(id={self.id}, user_id={self.user_id}, title='{self.title}')>"


class ChatMessage(Base):
    """Individual conversational turn belonging to a chat session."""

    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    session_id = Column(
        Integer,
        ForeignKey("chat_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    role = Column(String(50), nullable=False)
    content = Column(Text, nullable=False)
    source_metadata = Column(JSON, nullable=True)
    created_at = Column(UTCDateTime, default=utc_now, nullable=False)

    __table_args__ = (
        CheckConstraint("role IN ('user', 'assistant', 'system')", name="valid_chat_role"),
    )

    # Relationships
    session = relationship("ChatSession", back_populates="messages")

    def __repr__(self) -> str:
        return f"<ChatMessage(id={self.id}, session_id={self.session_id}, role='{self.role}')>"
