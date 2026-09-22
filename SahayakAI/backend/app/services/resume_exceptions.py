"""
Resume Analyzer Domain Exceptions.
Provides controlled exceptions with HTTP status codes for resume operations.
"""

from typing import Any, Optional
from fastapi import status
from backend.app.exceptions import AppException


class ResumeError(AppException):
    """Base exception for resume analyzer domain."""

    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        error_code: str = "RESUME_ERROR",
        details: Optional[Any] = None,
    ):
        super().__init__(message=message, status_code=status_code, error_code=error_code, details=details)


class ResumeNotFoundError(ResumeError):
    """Raised when a requested resume does not exist."""

    def __init__(self, message: str = "Resume not found", resume_id: Optional[int] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_404_NOT_FOUND,
            error_code="RESUME_NOT_FOUND",
            details={"resume_id": resume_id} if resume_id is not None else None,
        )


class ResumeAccessDeniedError(ResumeError):
    """Raised when a user attempts to access another user's resume."""

    def __init__(self, message: str = "Access to resume denied", resume_id: Optional[int] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_403_FORBIDDEN,
            error_code="RESUME_ACCESS_DENIED",
            details={"resume_id": resume_id} if resume_id is not None else None,
        )


class ResumeAnalysisNotFoundError(ResumeError):
    """Raised when an analysis record does not exist."""

    def __init__(self, message: str = "Resume analysis not found", analysis_id: Optional[int] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_404_NOT_FOUND,
            error_code="ANALYSIS_NOT_FOUND",
            details={"analysis_id": analysis_id} if analysis_id is not None else None,
        )


class ResumeAnalysisAccessDeniedError(ResumeError):
    """Raised when a user attempts to view another user's analysis."""

    def __init__(self, message: str = "Access to resume analysis denied", analysis_id: Optional[int] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_403_FORBIDDEN,
            error_code="ANALYSIS_ACCESS_DENIED",
            details={"analysis_id": analysis_id} if analysis_id is not None else None,
        )


class ResumeProcessingError(ResumeError):
    """Raised when resume extraction or validation fails."""

    def __init__(self, message: str, details: Optional[Any] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
            error_code="RESUME_PROCESSING_ERROR",
            details=details,
        )
