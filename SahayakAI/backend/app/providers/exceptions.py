"""
AI Provider Exceptions Module.
Defines controlled, sanitized exceptions for AI provider operations.
Prevents leaking of API keys, authorization tokens, or sensitive payloads.
"""

import re
from typing import Any, Optional
from fastapi import status
from backend.app.exceptions import AppException


def sanitize_sensitive_data(message: str) -> str:
    """
    Remove or mask potential API keys, authorization tokens, and credentials from error strings.
    """
    if not isinstance(message, str):
        message = str(message)

    # Mask OpenAI-style keys (sk-...)
    message = re.sub(r"sk-[a-zA-Z0-9_\-]{16,}", "sk-***REDACTED***", message)
    # Mask Gemini-style keys (AIza...)
    message = re.sub(r"AIza[a-zA-Z0-9_\-]{16,}", "AIza***REDACTED***", message)
    # Mask Bearer tokens
    message = re.sub(r"Bearer\s+[a-zA-Z0-9_\-\.]{10,}", "Bearer ***REDACTED***", message, flags=re.IGNORECASE)
    # Mask key=... or api_key=... patterns
    message = re.sub(r'(api[_-]?key["\']?\s*[:=]\s*["\']?)[a-zA-Z0-9_\-]{8,}(["\']?)', r"\1***REDACTED***\2", message, flags=re.IGNORECASE)
    # Mask authorization headers
    message = re.sub(r'(authorization["\']?\s*[:=]\s*["\']?)[^"\']{8,}(["\']?)', r"\1***REDACTED***\2", message, flags=re.IGNORECASE)

    return message


class ProviderError(AppException):
    """Base exception for all AI provider-related failures."""

    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        error_code: str = "PROVIDER_ERROR",
        details: Optional[Any] = None,
    ):
        sanitized_message = sanitize_sensitive_data(message)
        super().__init__(
            message=sanitized_message,
            status_code=status_code,
            error_code=error_code,
            details=details,
        )


class ProviderConfigurationError(ProviderError):
    """Raised when provider configuration or required credentials are missing/invalid."""

    def __init__(self, message: str, details: Optional[Any] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_code="PROVIDER_CONFIGURATION_ERROR",
            details=details,
        )


class UnsupportedProviderError(ProviderConfigurationError):
    """Raised when an unknown or unsupported provider name is specified."""

    def __init__(self, message: str, details: Optional[Any] = None):
        super().__init__(
            message=message,
            details=details,
        )
        self.status_code = status.HTTP_400_BAD_REQUEST
        self.error_code = "UNSUPPORTED_PROVIDER_ERROR"


class ProviderAuthenticationError(ProviderError):
    """Raised when provider API key authentication or authorization fails."""

    def __init__(self, message: str = "Provider authentication failed. Verify API key credentials.", details: Optional[Any] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_502_BAD_GATEWAY,
            error_code="PROVIDER_AUTHENTICATION_ERROR",
            details=details,
        )


class ProviderTimeoutError(ProviderError):
    """Raised when an AI provider call times out."""

    def __init__(self, message: str = "AI provider request timed out.", details: Optional[Any] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            error_code="PROVIDER_TIMEOUT_ERROR",
            details=details,
        )


class ProviderRequestError(ProviderError):
    """Raised when the provider rejects the request or external network/service error occurs."""

    def __init__(self, message: str, details: Optional[Any] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_502_BAD_GATEWAY,
            error_code="PROVIDER_REQUEST_ERROR",
            details=details,
        )


class ProviderResponseError(ProviderError):
    """Raised when provider response is malformed, truncated, or unparseable."""

    def __init__(self, message: str = "AI provider returned a malformed or empty response.", details: Optional[Any] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_502_BAD_GATEWAY,
            error_code="PROVIDER_RESPONSE_ERROR",
            details=details,
        )
