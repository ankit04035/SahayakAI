"""Password hashing and opaque browser-session lifecycle."""

import hashlib
import hmac
import secrets
import time
from typing import Optional, Tuple
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from backend.app.config import get_settings
from backend.app.models.user import AuthSession, User, UserCredential

PASSWORD_SCRYPT_N = 1 << 14
PASSWORD_SCRYPT_R = 8
PASSWORD_SCRYPT_P = 1
SESSION_TOKEN_BYTES = 32
CSRF_TOKEN_BYTES = 32


def normalize_email(email: str) -> str:
    return email.strip().casefold()


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.scrypt(
        password.encode("utf-8"),
        salt=salt,
        n=PASSWORD_SCRYPT_N,
        r=PASSWORD_SCRYPT_R,
        p=PASSWORD_SCRYPT_P,
        dklen=64,
    )
    return f"scrypt${PASSWORD_SCRYPT_N}${PASSWORD_SCRYPT_R}${PASSWORD_SCRYPT_P}${salt.hex()}${digest.hex()}"


def verify_password(password: str, encoded_hash: str) -> bool:
    try:
        algorithm, n, r, p, salt_hex, digest_hex = encoded_hash.split("$", 5)
        if algorithm != "scrypt":
            return False
        digest = hashlib.scrypt(
            password.encode("utf-8"),
            salt=bytes.fromhex(salt_hex),
            n=int(n),
            r=int(r),
            p=int(p),
            dklen=len(bytes.fromhex(digest_hex)),
        )
        return hmac.compare_digest(digest.hex(), digest_hex)
    except (ValueError, TypeError, MemoryError):
        return False


def register_user(db: Session, name: str, email: str, password: str) -> User:
    normalized_email = normalize_email(email)
    existing = db.query(User).filter(func.lower(User.email) == normalized_email).first()
    if existing:
        raise ValueError("An account with this email already exists.")

    user = User(name=name.strip(), email=normalized_email)
    db.add(user)
    try:
        db.flush()
        db.add(UserCredential(user_id=user.id, password_hash=hash_password(password)))
        db.commit()
        db.refresh(user)
    except IntegrityError as exc:
        db.rollback()
        raise ValueError("An account with this email already exists.") from exc
    return user


def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    normalized_email = normalize_email(email)
    user = db.query(User).filter(func.lower(User.email) == normalized_email).first()
    credential = db.query(UserCredential).filter(UserCredential.user_id == user.id).first() if user else None
    if not credential or not verify_password(password, credential.password_hash):
        return None
    return user


def create_session(db: Session, user_id: int) -> Tuple[str, str, AuthSession]:
    token = secrets.token_urlsafe(SESSION_TOKEN_BYTES)
    csrf_token = secrets.token_urlsafe(CSRF_TOKEN_BYTES)
    session = AuthSession(
        user_id=user_id,
        token_hash=hashlib.sha256(token.encode("utf-8")).hexdigest(),
        csrf_hash=hashlib.sha256(csrf_token.encode("utf-8")).hexdigest(),
        expires_at=int(time.time()) + get_settings().AUTH_SESSION_DAYS * 86400,
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return token, csrf_token, session


def get_session(db: Session, token: Optional[str]) -> Optional[AuthSession]:
    if not token:
        return None
    token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
    session = db.query(AuthSession).filter(AuthSession.token_hash == token_hash).first()
    if session and session.expires_at <= int(time.time()):
        db.delete(session)
        db.commit()
        return None
    return session


def rotate_csrf_token(db: Session, session: AuthSession) -> str:
    csrf_token = secrets.token_urlsafe(CSRF_TOKEN_BYTES)
    session.csrf_hash = hashlib.sha256(csrf_token.encode("utf-8")).hexdigest()
    db.commit()
    return csrf_token


def verify_csrf_token(session: AuthSession, token: Optional[str]) -> bool:
    if not token:
        return False
    token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
    return hmac.compare_digest(session.csrf_hash, token_hash)


def revoke_session(db: Session, session: AuthSession) -> None:
    db.delete(session)
    db.commit()
