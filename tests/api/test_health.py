"""
Tests for Health Check API Endpoint.
Verifies system liveness, database connectivity status, AI provider mode, and OpenAPI docs.
"""

from unittest.mock import patch
import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.config import get_settings


@pytest.fixture
def client():
    """Fixture providing a test client for the FastAPI application."""
    with TestClient(app) as test_client:
        yield test_client


def test_app_imports_successfully():
    """Verify FastAPI application instance is created with expected configuration."""
    settings = get_settings()
    assert app.title == settings.APP_NAME
    assert app.version == settings.APP_VERSION


def test_health_endpoint_success(client):
    """Verify GET /api/health returns 200 OK with all required fields."""
    settings = get_settings()
    response = client.get("/api/health")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "ok"
    assert data["database"] == "ok"
    assert data["ai_provider"] == settings.AI_PROVIDER
    assert data["version"] == settings.APP_VERSION


def test_demo_provider_mode_without_keys(client):
    """Verify application operates in Demo mode without requiring any external API keys."""
    settings = get_settings()
    assert settings.AI_PROVIDER == "demo"
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["ai_provider"] == "demo"


def test_health_endpoint_degraded_database(client):
    """Verify GET /api/health does not crash and returns 503 when database is unavailable."""
    with patch("backend.app.routes.health.check_database_connection", return_value=(False, "Database disk I/O error")):
        response = client.get("/api/health")
        assert response.status_code == 503

        data = response.json()
        assert data["status"] == "degraded"
        assert data["database"] == "error"
        assert "ai_provider" in data
        assert "version" in data


def test_docs_and_redoc_endpoints(client):
    """Verify interactive API documentation endpoints /docs and /redoc are accessible."""
    docs_res = client.get("/docs")
    assert docs_res.status_code == 200

    redoc_res = client.get("/redoc")
    assert redoc_res.status_code == 200

    openapi_res = client.get("/openapi.json")
    assert openapi_res.status_code == 200
    assert "paths" in openapi_res.json()
