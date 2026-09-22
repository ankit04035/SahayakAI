"""
User Model Definition.
Represents user profiles and account owners for all related application entities.
"""

from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from backend.app.database import Base
from backend.app.models.base import TimestampMixin


class User(Base, TimestampMixin):
    """User account entity owning documents, chat sessions, resumes, and career profiles."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)

    # Relationships
    documents = relationship(
        "Document",
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    chat_sessions = relationship(
        "ChatSession",
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    resumes = relationship(
        "Resume",
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    career_profiles = relationship(
        "CareerProfile",
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email='{self.email}', name='{self.name}')>"
