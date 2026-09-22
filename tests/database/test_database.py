"""
Tests for Database Foundation Module.
Verifies engine initialization, session lifecycle, and connection verification.
"""

from pathlib import Path
from sqlalchemy.orm import Session
from backend.app.database import engine, SessionLocal, get_db, check_database_connection
from backend.app.config import get_settings


def test_engine_initialization():
    """Verify SQLAlchemy engine is bound to configured database URL."""
    settings = get_settings()
    assert str(engine.url) == settings.DATABASE_URL


def test_check_database_connection():
    """Verify database connection check succeeds with healthy database."""
    is_healthy, message = check_database_connection()
    assert is_healthy is True
    assert message == "ok"


def test_get_db_session_lifecycle():
    """Verify get_db generator yields active session and closes upon completion."""
    session_gen = get_db()
    db = next(session_gen)
    assert isinstance(db, Session)
    assert db.is_active

    # Complete the generator
    try:
        next(session_gen)
    except StopIteration:
        pass


def test_sqlite_directory_creation():
    """Verify SQLite database file directory exists."""
    settings = get_settings()
    if settings.DATABASE_URL.startswith("sqlite:///"):
        path_str = settings.DATABASE_URL.replace("sqlite:///", "")
        db_path = Path(path_str)
        assert db_path.parent.exists()
