"""
User Model Definition.
Represents user profiles and account owners for all related application entities.
"""

from sqlalchemy import BigInteger, Column, ForeignKey, Integer, String
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
    credential = relationship(
        "UserCredential",
        back_populates="user",
        cascade="all, delete-orphan",
        uselist=False,
    )
    auth_sessions = relationship(
        "AuthSession",
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email='{self.email}', name='{self.name}')>"


class UserCredential(Base):
    """Password hash stored separately from public user profile data."""

    __tablename__ = "user_credentials"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    user = relationship("User", back_populates="credential")


class AuthSession(Base, TimestampMixin):
    """Revocable browser session containing hashes, never raw auth tokens."""

    __tablename__ = "auth_sessions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    token_hash = Column(String(64), unique=True, nullable=False, index=True)
    csrf_hash = Column(String(64), nullable=False)
    expires_at = Column(BigInteger, nullable=False, index=True)
    user = relationship("User", back_populates="auth_sessions")
