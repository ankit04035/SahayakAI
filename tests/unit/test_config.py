"""
Unit Tests for Configuration and Error Handling.
Verifies typed settings loading, CORS validation, and structured exception responses.
"""

import pytest
from pydantic import ValidationError
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.app.config import Settings, get_settings
from backend.app.exceptions import AppException, register_exception_handlers


def test_default_configuration():
    """Verify default configuration values match architecture specification."""
    settings = get_settings()
    assert settings.APP_NAME == "SahayakAI"
    assert settings.APP_VERSION == "0.1.0"
    assert settings.AI_PROVIDER == "demo"
    assert settings.ENVIRONMENT == "development"
    assert settings.MAX_UPLOAD_SIZE_MB == 10
    assert "sqlite" in settings.DATABASE_URL
    assert isinstance(settings.CORS_ORIGINS, list)


def test_custom_cors_origins_parsing():
    """Verify CORS origins string is parsed into list of trimmed strings."""
    # Comma-separated string
    s1 = Settings(CORS_ORIGINS="http://localhost:5173, http://localhost:3000")
    assert s1.CORS_ORIGINS == ["http://localhost:5173", "http://localhost:3000"]

    # JSON array string
    s2 = Settings(CORS_ORIGINS='["http://localhost:5173", "http://localhost:3000"]')
    assert s2.CORS_ORIGINS == ["http://localhost:5173", "http://localhost:3000"]

    # Explicit list
    s3 = Settings(CORS_ORIGINS=["http://localhost:5173"])
    assert s3.CORS_ORIGINS == ["http://localhost:5173"]


def test_invalid_max_upload_size():
    """Verify invalid upload size raises ValidationError."""
    with pytest.raises(ValidationError):
        Settings(MAX_UPLOAD_SIZE_MB=0)

    with pytest.raises(ValidationError):
        Settings(MAX_UPLOAD_SIZE_MB=-5)

    with pytest.raises(ValidationError):
        Settings(MAX_UPLOAD_SIZE_MB=500)


def test_structured_error_response_for_app_exception():
    """Verify AppException yields standardized JSON error structure."""
    test_app = FastAPI()
    register_exception_handlers(test_app)

    @test_app.get("/trigger-error")
    def trigger_error():
        raise AppException(
            message="Custom failure occurred",
            status_code=400,
            error_code="CUSTOM_BAD_REQUEST",
            details={"field": "test_input"},
        )

    with TestClient(test_app) as client:
        response = client.get("/trigger-error")
        assert response.status_code == 400
        data = response.json()
        assert data["status"] == "error"
        assert data["error_code"] == "CUSTOM_BAD_REQUEST"
        assert data["message"] == "Custom failure occurred"
        assert data["details"] == {"field": "test_input"}


def test_structured_error_response_for_unhandled_exception():
    """Verify unhandled exceptions yield standardized 500 error without exposing stack trace."""
    test_app = FastAPI()
    register_exception_handlers(test_app)

    @test_app.get("/trigger-crash")
    def trigger_crash():
        # Raise unexpected error
        raise ZeroDivisionError("Divide by zero in internal calculation")

    with TestClient(test_app, raise_server_exceptions=False) as client:
        response = client.get("/trigger-crash")
        assert response.status_code == 500
        data = response.json()
        assert data["status"] == "error"
        assert data["error_code"] == "INTERNAL_SERVER_ERROR"
        assert "internal server error" in data["message"].lower()
        # Verify stack trace is NOT leaked to client
        assert "ZeroDivisionError" not in response.text
        assert "Traceback" not in response.text
