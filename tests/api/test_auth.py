from fastapi.testclient import TestClient
from uuid import uuid4

from backend.app.config import get_settings
from backend.app.database import SessionLocal
from backend.app.main import app
from backend.app.models.user import User


def test_register_login_and_logout_use_hashed_passwords_and_revocable_sessions(monkeypatch):
    settings = get_settings()
    monkeypatch.setattr(settings, "ENVIRONMENT", "production")
    monkeypatch.setattr(settings, "AUTH_REQUIRED", True)

    with TestClient(app) as client:
        payload = {
            "name": "Auth Test User",
            "email": f"auth-flow-{uuid4().hex}@example.com",
            "password": "Correct Horse Battery 17!",
        }
        assert client.get("/api/auth/me").status_code == 200
        assert client.get("/api/auth/me").json() is None
        registered = client.post("/api/auth/register", json=payload)
        assert registered.status_code == 201
        assert registered.json()["user"]["email"] == payload["email"]
        assert "password" not in registered.json()["user"]
        assert registered.cookies.get("sahayakai_session")
        assert "httponly" in registered.headers["set-cookie"].lower()
        csrf_token = registered.json()["csrf_token"]

        assert client.get("/api/documents").status_code == 200
        assert client.get("/api/documents", headers={"X-User-Id": "999999"}).status_code == 403
        assert client.post("/api/chat/sessions", json={"title": "blocked"}).status_code == 403

        duplicate = client.post("/api/auth/register", json=payload)
        assert duplicate.status_code == 409

        logout = client.post("/api/auth/logout", headers={"X-CSRF-Token": csrf_token})
        assert logout.status_code == 204
        signed_out = client.get("/api/auth/me")
        assert signed_out.status_code == 200
        assert signed_out.json() is None

        login = client.post("/api/auth/login", json={"email": payload["email"], "password": payload["password"]})
        assert login.status_code == 200
        assert login.cookies.get("sahayakai_session")
        assert client.get("/api/auth/me").json()["id"] == registered.json()["user"]["id"]
        assert client.post("/api/auth/logout").status_code == 403
        assert client.post(
            "/api/auth/logout",
            headers={"X-CSRF-Token": login.json()["csrf_token"]},
        ).status_code == 204

    db = SessionLocal()
    try:
        test_user = db.query(User).filter(User.email == payload["email"]).first()
        if test_user:
            db.delete(test_user)
            db.commit()
    finally:
        db.close()


def test_registration_rejects_short_passwords():
    with TestClient(app) as client:
        response = client.post(
            "/api/auth/register",
            json={"name": "Short Password", "email": "short-password@example.com", "password": "short"},
        )
    assert response.status_code == 422
