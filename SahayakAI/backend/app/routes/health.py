"""
Health Check API Route.
Provides system liveness, database connectivity, AI provider mode, and version status.
"""

from typing import Dict, Any
from fastapi import APIRouter, Response, status
from pydantic import BaseModel, Field

from backend.app.config import get_settings
from backend.app.database import check_database_connection

router = APIRouter(tags=["Health"])


class HealthResponse(BaseModel):
    """Health check response payload schema."""

    status: str = Field(..., description="Overall service status: ok, degraded")
    database: str = Field(..., description="Database connection status: ok, error")
    ai_provider: str = Field(..., description="Active AI provider mode")
    version: str = Field(..., description="Application semantic version")


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Application Health & Status",
    description="Returns service liveness, database connectivity, active AI provider mode, and semantic version.",
    responses={
        200: {"description": "Service is healthy and fully operational."},
        503: {"description": "Service is degraded (e.g. database connectivity failure)."},
    },
)
async def get_health(response: Response) -> Dict[str, Any]:
    """Inspect and return operational health metrics."""
    settings = get_settings()

    db_healthy, _ = check_database_connection()

    if db_healthy:
        response.status_code = status.HTTP_200_OK
        overall_status = "ok"
        db_status = "ok"
    else:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        overall_status = "degraded"
        db_status = "error"

    return {
        "status": overall_status,
        "database": db_status,
        "ai_provider": settings.AI_PROVIDER,
        "version": settings.APP_VERSION,
    }
