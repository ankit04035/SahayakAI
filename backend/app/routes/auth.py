"""Registration, login, current-account, CSRF, and logout endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session
from backend.app.config import get_settings
from backend.app.database import get_db
from backend.app.models.user import AuthSession, User
from backend.app.schemas.auth import AuthResponse, AuthUserRead, CsrfResponse, LoginRequest, RegisterRequest
from backend.app.services.auth_service import (
    authenticate_user,
    create_session,
    get_session,
    register_user,
    revoke_session,
    rotate_csrf_token,
    verify_csrf_token,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])
COOKIE_NAME = "sahayakai_session"


def _check_origin(request: Request) -> None:
    origin = request.headers.get("origin")
    if origin and origin not in get_settings().CORS_ORIGINS:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Origin is not allowed.")


def _set_session_cookie(response: Response, token: str) -> None:
    settings = get_settings()
    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        max_age=settings.AUTH_SESSION_DAYS * 86400,
        httponly=True,
        secure=settings.AUTH_COOKIE_SECURE,
        samesite="none" if settings.AUTH_COOKIE_SECURE else "lax",
        path="/api",
    )


def _current_session(request: Request, db: Session) -> AuthSession | None:
    session = get_session(db, request.cookies.get(COOKIE_NAME))
    if not session:
        return None  # Return None instead of raising an exception
    return session


def _check_csrf(request: Request, session: AuthSession) -> None:
    if not verify_csrf_token(session, request.headers.get("X-CSRF-Token")):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Your session expired. Refresh and try again.")


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, request: Request, response: Response, db: Session = Depends(get_db)) -> AuthResponse:
    _check_origin(request)
    try:
        user = register_user(db, payload.name, str(payload.email), payload.password)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    token, csrf_token, _ = create_session(db, user.id)
    _set_session_cookie(response, token)
    return AuthResponse(user=AuthUserRead.model_validate(user), csrf_token=csrf_token)


@router.post("/login", response_model=AuthResponse)
def login(payload: LoginRequest, request: Request, response: Response, db: Session = Depends(get_db)) -> AuthResponse:
    _check_origin(request)
    user = authenticate_user(db, str(payload.email), payload.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Email or password is incorrect.")
    token, csrf_token, _ = create_session(db, user.id)
    _set_session_cookie(response, token)
    return AuthResponse(user=AuthUserRead.model_validate(user), csrf_token=csrf_token)


@router.get("/me", response_model=AuthUserRead | None)
def current_user(request: Request, db: Session = Depends(get_db)) -> AuthUserRead | None:
    session = _current_session(request, db)
    if session is None:
        return None
    user = db.query(User).filter(User.id == session.user_id).first()
    return AuthUserRead.model_validate(user) if user else None


@router.get("/csrf", response_model=CsrfResponse)
def refresh_csrf(request: Request, db: Session = Depends(get_db)) -> CsrfResponse:
    session = _current_session(request, db)
    if session is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Please sign in to continue.")
    return CsrfResponse(csrf_token=rotate_csrf_token(db, session))


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(request: Request, response: Response, db: Session = Depends(get_db)) -> Response:
    session = _current_session(request, db)
    if session is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Please sign in to continue.")
    _check_csrf(request, session)
    revoke_session(db, session)
    response.delete_cookie(COOKIE_NAME, path="/api", secure=get_settings().AUTH_COOKIE_SECURE, httponly=True, samesite="none" if get_settings().AUTH_COOKIE_SECURE else "lax")
    response.status_code = status.HTTP_204_NO_CONTENT
    return response
