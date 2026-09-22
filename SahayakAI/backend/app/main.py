"""
FastAPI Application Entrypoint.
Initializes the application instance, middleware, exception handlers, and routing.
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.config import get_settings
from backend.app.database import init_db
from backend.app.exceptions import register_exception_handlers
from backend.app.logging_config import setup_logging
from backend.app.routes.health import router as health_router

settings = get_settings()
logger = setup_logging(settings.LOG_LEVEL)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Lifespan context manager for application startup and shutdown events."""
    logger.info(
        "Starting %s v%s in %s mode",
        settings.APP_NAME,
        settings.APP_VERSION,
        settings.ENVIRONMENT,
    )
    logger.info("Configured AI Provider: %s", settings.AI_PROVIDER)
    try:
        init_db()
        logger.info("Database schema initialized successfully.")
    except Exception as exc:
        logger.error("Database initialization encountered an error: %s", exc, exc_info=True)

    yield
    logger.info("Shutting down %s", settings.APP_NAME)


def create_app() -> FastAPI:
    """Factory creating and configuring the FastAPI application instance."""
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # Configure CORS using strict origin settings
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
        allow_headers=["*"],
    )

    # Register centralized exception handlers
    register_exception_handlers(app)

    # Register API routers
    app.include_router(health_router, prefix="/api")

    return app


app = create_app()
