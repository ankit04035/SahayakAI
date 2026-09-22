"""
SQLAlchemy Models Package.
Exports all application database models and registers them with Base metadata.
"""

from backend.app.models.base import TimestampMixin, utc_now
from backend.app.models.user import User
from backend.app.models.document import Document, DocumentChunk
from backend.app.models.chat import ChatSession, ChatMessage
from backend.app.models.resume import Resume, ResumeAnalysis
from backend.app.models.career import CareerProfile, Roadmap

__all__ = [
    "TimestampMixin",
    "utc_now",
    "User",
    "Document",
    "DocumentChunk",
    "ChatSession",
    "ChatMessage",
    "Resume",
    "ResumeAnalysis",
    "CareerProfile",
    "Roadmap",
]
