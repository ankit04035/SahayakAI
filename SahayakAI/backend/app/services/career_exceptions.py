"""
Career Profile and Roadmap Domain Exceptions.
Provides controlled exceptions with HTTP status codes for career operations.
"""

from typing import Any, Optional
from fastapi import status
from backend.app.exceptions import AppException


class CareerError(AppException):
    """Base exception for career profile and roadmap domain."""

    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        error_code: str = "CAREER_ERROR",
        details: Optional[Any] = None,
    ):
        super().__init__(message=message, status_code=status_code, error_code=error_code, details=details)


class CareerProfileNotFoundError(CareerError):
    """Raised when a user's career profile is not found."""

    def __init__(self, message: str = "Career profile not found", profile_id: Optional[int] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_404_NOT_FOUND,
            error_code="PROFILE_NOT_FOUND",
            details={"profile_id": profile_id} if profile_id is not None else None,
        )


class CareerProfileAccessDeniedError(CareerError):
    """Raised when a user attempts to access another user's career profile."""

    def __init__(self, message: str = "Access to career profile denied", profile_id: Optional[int] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_403_FORBIDDEN,
            error_code="PROFILE_ACCESS_DENIED",
            details={"profile_id": profile_id} if profile_id is not None else None,
        )


class RoadmapNotFoundError(CareerError):
    """Raised when a requested career roadmap is not found."""

    def __init__(self, message: str = "Career roadmap not found", roadmap_id: Optional[int] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_404_NOT_FOUND,
            error_code="ROADMAP_NOT_FOUND",
            details={"roadmap_id": roadmap_id} if roadmap_id is not None else None,
        )


class RoadmapAccessDeniedError(CareerError):
    """Raised when a user attempts to access another user's career roadmap."""

    def __init__(self, message: str = "Access to career roadmap denied", roadmap_id: Optional[int] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_403_FORBIDDEN,
            error_code="ROADMAP_ACCESS_DENIED",
            details={"roadmap_id": roadmap_id} if roadmap_id is not None else None,
        )


class RoadmapGenerationError(CareerError):
    """Raised when roadmap generation fails due to invalid parameters or state."""

    def __init__(self, message: str, details: Optional[Any] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
            error_code="ROADMAP_GENERATION_ERROR",
            details=details,
        )


class InvalidCareerProfileError(CareerError):
    """Raised when career profile data violates business requirements."""

    def __init__(self, message: str, details: Optional[Any] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
            error_code="INVALID_CAREER_PROFILE",
            details=details,
        )
