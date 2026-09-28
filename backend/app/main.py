"""
FastAPI Application Entrypoint.
Initializes the application instance, middleware, exception handlers, and routing.
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from backend.app.config import get_settings
from backend.app.database import SessionLocal, init_db
from backend.app.exceptions import register_exception_handlers
from backend.app.logging_config import setup_logging
from backend.app.routes.health import router as health_router
from backend.app.routes.documents import router as documents_router
from backend.app.routes.chat import router as chat_router
from backend.app.routes.resumes import router as resumes_router
from backend.app.routes.career import router as career_router
from backend.app.routes.auth import COOKIE_NAME, router as auth_router
from backend.app.services.auth_service import get_session, verify_csrf_token

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
    app.include_router(auth_router, prefix="/api")
    app.include_router(health_router, prefix="/api")
    app.include_router(documents_router, prefix="/api")
    app.include_router(chat_router, prefix="/api")
    app.include_router(resumes_router, prefix="/api")
    app.include_router(career_router, prefix="/api")

    @app.middleware("http")
    async def authenticate_api_request(request: Request, call_next):
        path = request.url.path
        if not path.startswith("/api/") or path == "/api/health" or path.startswith("/api/auth/") or request.method == "OPTIONS":
            return await call_next(request)

        if not settings.AUTH_REQUIRED or settings.ENVIRONMENT == "test":
            return await call_next(request)

        origin = request.headers.get("origin")
        if origin and origin not in settings.CORS_ORIGINS:
            return JSONResponse(status_code=403, content={"detail": "Origin is not allowed."})

        db = SessionLocal()
        try:
            auth_session = get_session(db, request.cookies.get(COOKIE_NAME))
            if not auth_session:
                return JSONResponse(status_code=401, content={"detail": "Please sign in to continue."})

            requested_user_id = request.headers.get("x-user-id")
            if requested_user_id and requested_user_id != str(auth_session.user_id):
                return JSONResponse(status_code=403, content={"detail": "You cannot access another account."})

            if request.method in {"POST", "PUT", "PATCH", "DELETE"}:
                csrf_token = request.headers.get("x-csrf-token")
                if not verify_csrf_token(auth_session, csrf_token):
                    return JSONResponse(status_code=403, content={"detail": "Your session expired. Refresh and try again."})

            request.scope["headers"] = list(request.scope["headers"]) + [
                (b"x-user-id", str(auth_session.user_id).encode("ascii")),
            ]
            return await call_next(request)
        finally:
            db.close()

    return app


app = create_app()
