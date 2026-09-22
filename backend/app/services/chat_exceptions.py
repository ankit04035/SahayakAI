"""
Chat and Study Assistant Domain Exceptions.
Defines domain-specific exception types mapped to appropriate HTTP status codes.
"""

from typing import Any, Optional
from fastapi import status
from backend.app.exceptions import AppException


class ChatError(AppException):
    """Base exception for all chat and study assistant errors."""

    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        error_code: str = "CHAT_ERROR",
        details: Optional[Any] = None,
    ):
        super().__init__(message=message, status_code=status_code, error_code=error_code, details=details)


class ChatSessionNotFoundError(ChatError):
    """Raised when a requested chat session does not exist."""

    def __init__(self, message: str = "Chat session not found", session_id: Optional[int] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_404_NOT_FOUND,
            error_code="SESSION_NOT_FOUND",
            details={"session_id": session_id} if session_id is not None else None,
        )


class ChatAccessDeniedError(ChatError):
    """Raised when a user attempts to access a session belonging to another user."""

    def __init__(self, message: str = "Access to chat session denied", session_id: Optional[int] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_403_FORBIDDEN,
            error_code="SESSION_ACCESS_DENIED",
            details={"session_id": session_id} if session_id is not None else None,
        )


class ChatMessageValidationError(ChatError):
    """Raised when a chat message violates input constraints."""

    def __init__(self, message: str, details: Optional[Any] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
            error_code="INVALID_MESSAGE",
            details=details,
        )


class DocumentOwnershipError(ChatError):
    """Raised when attempting to associate a session with a document owned by another user."""

    def __init__(self, message: str = "Document does not belong to the user", document_id: Optional[int] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_403_FORBIDDEN,
            error_code="DOCUMENT_ACCESS_DENIED",
            details={"document_id": document_id} if document_id is not None else None,
        )


class ChatDocumentNotFoundError(ChatError):
    """Raised when the document specified for a chat session does not exist."""

    def __init__(self, message: str = "Associated document not found", document_id: Optional[int] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_404_NOT_FOUND,
            error_code="DOCUMENT_NOT_FOUND",
            details={"document_id": document_id} if document_id is not None else None,
        )
