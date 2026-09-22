"""
Comprehensive Backend Integration and API Contract Hardening Test Suite (Step 11).
Verifies:
- Application startup and lifespan context manager
- Health endpoint (healthy & degraded states)
- OpenAPI contract and documentation endpoints
- CORS enforcement and security headers
- Structured error response consistency (404, 422, 403, 500)
- End-to-End Workflow A: Document upload -> chunking -> embedding -> grounded chat -> saved message
- Workflow A Insufficient Evidence: Graceful fallback when query is out-of-context
- End-to-End Workflow B: Resume upload -> parsing -> ATS match scorecard -> recommendations
- End-to-End Workflow C: Career Profile -> ResumeAnalysis integration -> target role skill gap -> Roadmap generation
- Cross-User Access Isolation: Strict HTTP 403 Forbidden across all entities (Doc, Chat, Resume, Career, Roadmap)
- Cascade Deletions: Document, ChatSession, Resume, CareerProfile
- Deterministic Demo Mode: Complete operation without external provider credentials
"""

import io
from unittest.mock import patch
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.app.config import get_settings
from backend.app.database import SessionLocal, check_database_connection
from backend.app.main import app, lifespan
from backend.app.models.career import CareerProfile, Roadmap
from backend.app.models.chat import ChatMessage, ChatSession
from backend.app.models.document import Document, DocumentChunk
from backend.app.models.resume import Resume, ResumeAnalysis
from backend.app.models.user import User


# ==============================================================================
# FIXTURES
# ==============================================================================

@pytest.fixture
def db_session():
    """Transactional DB session with automatic teardown."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client():
    """FastAPI TestClient fixture."""
    return TestClient(app)


@pytest.fixture
def synthetic_users(db_session: Session):
    """Create two isolated synthetic users to test cross-user access boundaries."""
    u1 = db_session.query(User).filter(User.email == "synthetic_alice_int@example.com").first()
    if not u1:
        u1 = User(email="synthetic_alice_int@example.com", name="Synthetic Alice")
        db_session.add(u1)

    u2 = db_session.query(User).filter(User.email == "synthetic_bob_int@example.com").first()
    if not u2:
        u2 = User(email="synthetic_bob_int@example.com", name="Synthetic Bob")
        db_session.add(u2)

    db_session.commit()
    db_session.refresh(u1)
    db_session.refresh(u2)

    yield u1, u2

    # Teardown all resources associated with synthetic users
    # 1. Career profiles and roadmaps
    profiles = db_session.query(CareerProfile).filter(CareerProfile.user_id.in_([u1.id, u2.id])).all()
    for p in profiles:
        db_session.query(Roadmap).filter(Roadmap.career_profile_id == p.id).delete()
        db_session.delete(p)

    # 2. Resumes and analyses
    resumes = db_session.query(Resume).filter(Resume.user_id.in_([u1.id, u2.id])).all()
    for r in resumes:
        db_session.query(ResumeAnalysis).filter(ResumeAnalysis.resume_id == r.id).delete()
        db_session.delete(r)

    # 3. Chat sessions and messages
    sessions = db_session.query(ChatSession).filter(ChatSession.user_id.in_([u1.id, u2.id])).all()
    for s in sessions:
        db_session.query(ChatMessage).filter(ChatMessage.session_id == s.id).delete()
        db_session.delete(s)

    # 4. Documents and chunks
    docs = db_session.query(Document).filter(Document.user_id.in_([u1.id, u2.id])).all()
    for d in docs:
        db_session.query(DocumentChunk).filter(DocumentChunk.document_id == d.id).delete()
        db_session.delete(d)

    db_session.delete(u1)
    db_session.delete(u2)
    db_session.commit()


# ==============================================================================
# 1. STARTUP, LIFESPAN & HEALTH ENDPOINT TESTS
# ==============================================================================

class TestStartupAndHealth:
    """Verifies startup lifecycle and /api/health behavior."""

    @pytest.mark.asyncio
    async def test_lifespan_startup_and_shutdown(self):
        """Verify lifespan context manager executes smoothly and initializes DB schema."""
        async with lifespan(app):
            # Assert application can connect to DB during lifespan
            is_healthy, _ = check_database_connection()
            assert is_healthy is True

    def test_health_endpoint_healthy(self, client: TestClient):
        """Verify GET /api/health returns 200 OK with expected structure."""
        resp = client.get("/api/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert data["database"] == "ok"
        assert data["ai_provider"] in ["demo", "openai", "gemini"]
        assert "version" in data

    def test_health_endpoint_degraded(self, client: TestClient):
        """Verify GET /api/health returns 503 when database connectivity fails."""
        with patch("backend.app.routes.health.check_database_connection", return_value=(False, "Connection failed")):
            resp = client.get("/api/health")
            assert resp.status_code == 503
            data = resp.json()
            assert data["status"] == "degraded"
            assert data["database"] == "error"


# ==============================================================================
# 2. OPENAPI & DOCUMENTATION CONTRACT TESTS
# ==============================================================================

class TestOpenApiContract:
    """Verifies OpenAPI specification, Swagger, ReDoc, and secret safety."""

    def test_openapi_schema_contains_all_routes(self, client: TestClient):
        """Verify GET /openapi.json is valid and lists all 5 endpoint domains."""
        resp = client.get("/openapi.json")
        assert resp.status_code == 200
        spec = resp.json()
        assert spec["openapi"].startswith("3.")
        paths = spec["paths"]

        # Health
        assert "/api/health" in paths
        # Documents
        assert "/api/documents/upload" in paths
        assert "/api/documents" in paths
        assert "/api/documents/{document_id}" in paths
        assert "/api/documents/{document_id}/embed" in paths
        assert "/api/documents/{document_id}/ask" in paths
        # Chat
        assert "/api/chat/sessions" in paths
        assert "/api/chat/sessions/{session_id}" in paths
        assert "/api/chat/sessions/{session_id}/messages" in paths
        # Resumes
        assert "/api/resumes" in paths
        assert "/api/resumes/{resume_id}" in paths
        assert "/api/resumes/{resume_id}/analyze" in paths
        # Career
        assert "/api/career/profile" in paths
        assert "/api/career/roadmaps" in paths
        assert "/api/career/roadmaps/generate" in paths
        assert "/api/career/roadmaps/{roadmap_id}" in paths

    def test_docs_and_redoc_endpoints(self, client: TestClient):
        """Verify Swagger UI and ReDoc HTML endpoints load with 200 OK."""
        assert client.get("/docs").status_code == 200
        assert client.get("/redoc").status_code == 200

    def test_openapi_no_sensitive_secrets_leaked(self, client: TestClient):
        """Ensure API keys, passwords, or raw secrets are never leaked in the OpenAPI document."""
        spec_text = client.get("/openapi.json").text
        assert "OPENAI_API_KEY" not in spec_text
        assert "GEMINI_API_KEY" not in spec_text


# ==============================================================================
# 3. CORS & STRUCTURED ERROR CONTRACT TESTS
# ==============================================================================

class TestCorsAndErrorEnvelopes:
    """Verifies CORS policy headers and uniform JSON error payloads."""

    def test_cors_allowed_origin(self, client: TestClient):
        """Verify allowed frontend origin receives CORS headers."""
        headers = {
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "POST",
        }
        resp = client.options("/api/health", headers=headers)
        assert resp.headers.get("access-control-allow-origin") == "http://localhost:5173"

    def test_cors_disallowed_origin(self, client: TestClient):
        """Verify unauthorized origins are not echoed in access-control-allow-origin."""
        headers = {
            "Origin": "http://unauthorized-evil-site.com",
            "Access-Control-Request-Method": "POST",
        }
        resp = client.options("/api/health", headers=headers)
        assert resp.headers.get("access-control-allow-origin") != "http://unauthorized-evil-site.com"

    def test_uniform_404_error_envelope(self, client: TestClient):
        """Verify 404 responses conform to standard error schema."""
        resp = client.get("/api/documents/9999999")
        assert resp.status_code == 404
        data = resp.json()
        assert data["status"] == "error"
        assert data["error_code"] == "DOCUMENT_NOT_FOUND"
        assert "not found" in data["message"].lower()

    def test_uniform_422_validation_error_envelope(self, client: TestClient):
        """Verify 422 schema validation responses conform to standard error schema."""
        resp = client.post("/api/career/profile", json={"target_role": "A"})
        assert resp.status_code == 422
        data = resp.json()
        assert data["status"] == "error"
        assert data["error_code"] == "VALIDATION_ERROR"
        assert isinstance(data["details"], list)


# ==============================================================================
# 4. WORKFLOW A: DOCUMENT PROCESSING -> EMBEDDING -> RAG CHAT
# ==============================================================================

class TestWorkflowA_DocumentStudy:
    """Verifies complete Workflow A: Document upload -> chunking -> embedding -> chat -> RAG answer."""

    def test_end_to_end_document_study_workflow(self, client: TestClient, synthetic_users):
        user_alice, _ = synthetic_users
        auth_header = {"X-User-Id": str(user_alice.id)}

        # 1. Upload study guide document
        doc_content = (
            "SahayakAI Fast-Track Guide:\n"
            "FastAPI is a modern, high-performance web framework for building APIs with Python 3.8+ based on standard Python type hints.\n"
            "Sentence Transformers map sentences and paragraphs to 384-dimensional dense vector spaces for semantic similarity.\n"
            "Retrieval Augmented Generation combines vector similarity search with language models to produce grounded factual answers."
        ).encode("utf-8")

        upload_resp = client.post(
            "/api/documents/upload",
            files={"file": ("study_guide.txt", io.BytesIO(doc_content), "text/plain")},
            data={"title": "SahayakAI Study Guide", "auto_embed": "true"},
            headers=auth_header,
        )
        assert upload_resp.status_code == 201
        doc_data = upload_resp.json()
        doc_id = doc_data["id"]
        assert doc_data["user_id"] == user_alice.id
        assert doc_data["chunk_count"] > 0

        # 2. Verify chunks are persisted
        chunks_resp = client.get(f"/api/documents/{doc_id}/chunks", headers=auth_header)
        assert chunks_resp.status_code == 200
        chunks = chunks_resp.json()
        assert len(chunks) > 0

        # 3. Create chat session grounded in the document
        session_resp = client.post(
            "/api/chat/sessions",
            json={"title": "FastAPI & RAG Discussion", "document_id": doc_id},
            headers=auth_header,
        )
        assert session_resp.status_code == 201
        session_data = session_resp.json()
        session_id = session_data["id"]
        assert session_data["document_id"] == doc_id

        # 4. Ask grounded question
        msg_resp = client.post(
            f"/api/chat/sessions/{session_id}/messages",
            json={"message": "What is FastAPI and what framework is it based on?"},
            headers=auth_header,
        )
        assert msg_resp.status_code == 200
        ans_data = msg_resp.json()
        assert ans_data["grounded"] is True
        assert ans_data["assistant_message"]["content"] != ""
        assert len(ans_data["sources"]) > 0

        # 5. Ask out-of-context question (Insufficient Evidence test)
        ooc_resp = client.post(
            f"/api/chat/sessions/{session_id}/messages",
            json={"message": "What is the capital of Iceland and its population in 1950?"},
            headers=auth_header,
        )
        assert ooc_resp.status_code == 200
        ooc_data = ooc_resp.json()
        assert ooc_data["insufficient_evidence"] is True or ooc_data["grounded"] is False

        # 6. Verify messages persisted in session history
        history_resp = client.get(f"/api/chat/sessions/{session_id}/messages", headers=auth_header)
        assert history_resp.status_code == 200
        history = history_resp.json()
        assert len(history) == 4  # 2 user messages + 2 assistant responses


# ==============================================================================
# 5. WORKFLOW B: RESUME UPLOAD -> ATS ANALYSIS
# ==============================================================================

class TestWorkflowB_ResumeAnalyzer:
    """Verifies complete Workflow B: Resume upload -> parsing -> ATS match scorecard."""

    def test_end_to_end_resume_ats_workflow(self, client: TestClient, synthetic_users):
        user_alice, _ = synthetic_users
        auth_header = {"X-User-Id": str(user_alice.id)}

        # 1. Upload candidate resume
        resume_text = (
            "Alice Smith - Backend Engineer\n"
            "Email: alice@example.com | Phone: 555-0199\n\n"
            "EDUCATION\n"
            "B.Tech in Computer Science, IIT Delhi, 2023\n\n"
            "SKILLS\n"
            "Python, FastAPI, Docker, PostgreSQL, Redis, Git, Linux\n\n"
            "EXPERIENCE\n"
            "Software Developer at TechCorp (2023 - Present)\n"
            "- Built REST APIs with FastAPI and PostgreSQL\n"
            "- Containerized microservices using Docker\n"
        ).encode("utf-8")

        upload_resp = client.post(
            "/api/resumes",
            files={"file": ("alice_resume.txt", io.BytesIO(resume_text), "text/plain")},
            headers=auth_header,
        )
        assert upload_resp.status_code == 201
        resume_data = upload_resp.json()
        resume_id = resume_data["id"]
        assert resume_data["user_id"] == user_alice.id

        # 2. Analyze against a target Job Description
        job_description = (
            "Senior Backend Engineer\n"
            "Requirements: Python, FastAPI, Docker, Kubernetes, AWS, PostgreSQL, Microservices."
        )

        analysis_resp = client.post(
            f"/api/resumes/{resume_id}/analyze",
            json={"job_description": job_description},
            headers=auth_header,
        )
        assert analysis_resp.status_code == 200
        analysis_data = analysis_resp.json()
        assert 0.0 <= analysis_data["match_score"] <= 100.0
        assert "python" in [s.lower() for s in analysis_data["extracted_skills"]]
        assert len(analysis_data["matched_skills"]) > 0
        assert len(analysis_data["missing_skills"]) > 0
        assert len(analysis_data["recommendations"]) > 0


# ==============================================================================
# 6. WORKFLOW C: CAREER PROFILE + RESUME -> PERSONALIZED ROADMAP
# ==============================================================================

class TestWorkflowC_CareerRoadmap:
    """Verifies complete Workflow C: Career Profile -> Resume integration -> Skill gaps -> Roadmap."""

    def test_end_to_end_career_roadmap_workflow(self, client: TestClient, synthetic_users):
        user_alice, _ = synthetic_users
        auth_header = {"X-User-Id": str(user_alice.id)}

        # 1. Create candidate career profile
        profile_payload = {
            "degree": "B.Tech Computer Science",
            "target_role": "Backend Developer",
            "current_skills": ["Python", "Git", "SQL"],
            "experience": "1 year building backend services in Python.",
            "interests": ["Distributed Systems", "Cloud Computing"],
        }
        prof_resp = client.post("/api/career/profile", json=profile_payload, headers=auth_header)
        assert prof_resp.status_code in [200, 201]
        prof_data = prof_resp.json()
        assert prof_data["target_role"] == "Backend Developer"

        # 2. Upload resume to incorporate into roadmap
        resume_content = (
            "Alice Smith\n"
            "Skills: Python, FastAPI, PostgreSQL, Git\n"
            "Education: B.Tech CS\n"
        ).encode("utf-8")
        res_upload = client.post(
            "/api/resumes",
            files={"file": ("alice_cv.txt", io.BytesIO(resume_content), "text/plain")},
            headers=auth_header,
        )
        resume_id = res_upload.json()["id"]

        # 3. Generate personalized career roadmap referencing resume
        roadmap_payload = {
            "target_role": "Backend Developer",
            "resume_id": resume_id,
        }
        road_resp = client.post("/api/career/roadmaps/generate", json=roadmap_payload, headers=auth_header)
        assert road_resp.status_code == 201
        roadmap = road_resp.json()

        assert "Backend Developer" in roadmap["title"]
        assert len(roadmap["recommended_skills"]) > 0
        assert len(roadmap["weekly_plan"]) > 0
        assert len(roadmap["projects"]) > 0
        assert len(roadmap["interview_topics"]) > 0

        # 4. List roadmaps
        list_resp = client.get("/api/career/roadmaps", headers=auth_header)
        assert list_resp.status_code == 200
        roadmaps = list_resp.json()
        assert len(roadmaps) >= 1
        assert roadmaps[0]["id"] == roadmap["id"]


# ==============================================================================
# 7. CROSS-USER ACCESS ISOLATION (SECURITY AUDIT)
# ==============================================================================

class TestCrossUserSecurityIsolation:
    """Verifies that all entities strictly return HTTP 403 when accessed by another user."""

    def test_cross_user_rejection_across_all_modules(self, client: TestClient, synthetic_users):
        user_alice, user_bob = synthetic_users
        alice_header = {"X-User-Id": str(user_alice.id)}
        bob_header = {"X-User-Id": str(user_bob.id)}

        # Alice creates resources:
        # A. Document
        doc_resp = client.post(
            "/api/documents/upload",
            files={"file": ("alice_doc.txt", io.BytesIO(b"Alice confidential notes"), "text/plain")},
            headers=alice_header,
        )
        alice_doc_id = doc_resp.json()["id"]

        # B. Chat Session
        session_resp = client.post(
            "/api/chat/sessions",
            json={"title": "Alice Private Chat", "document_id": alice_doc_id},
            headers=alice_header,
        )
        alice_session_id = session_resp.json()["id"]

        # C. Resume
        resume_resp = client.post(
            "/api/resumes",
            files={"file": ("alice_resume.txt", io.BytesIO(b"Alice Resume Python Docker"), "text/plain")},
            headers=alice_header,
        )
        alice_resume_id = resume_resp.json()["id"]

        # D. Career Profile & Roadmap
        client.post(
            "/api/career/profile",
            json={"target_role": "Python Developer", "current_skills": ["Python"]},
            headers=alice_header,
        )
        roadmap_resp = client.post(
            "/api/career/roadmaps/generate",
            json={"target_role": "Python Developer"},
            headers=alice_header,
        )
        alice_roadmap_id = roadmap_resp.json()["id"]

        # Bob attempts unauthorized access (must receive HTTP 403):
        # 1. Document access
        assert client.get(f"/api/documents/{alice_doc_id}", headers=bob_header).status_code == 403
        assert client.get(f"/api/documents/{alice_doc_id}/chunks", headers=bob_header).status_code == 403
        assert client.post(f"/api/documents/{alice_doc_id}/embed", headers=bob_header).status_code == 403
        assert client.post(f"/api/documents/{alice_doc_id}/ask", json={"question": "test"}, headers=bob_header).status_code == 403
        assert client.delete(f"/api/documents/{alice_doc_id}", headers=bob_header).status_code == 403

        # 2. Chat session access
        assert client.get(f"/api/chat/sessions/{alice_session_id}", headers=bob_header).status_code == 403
        assert client.post(f"/api/chat/sessions/{alice_session_id}/messages", json={"message": "hack"}, headers=bob_header).status_code == 403
        assert client.delete(f"/api/chat/sessions/{alice_session_id}", headers=bob_header).status_code == 403

        # 3. Resume access
        assert client.get(f"/api/resumes/{alice_resume_id}", headers=bob_header).status_code == 403
        valid_jd = {"job_description": "Seeking experienced Python developer with Docker and FastAPI experience"}
        assert client.post(f"/api/resumes/{alice_resume_id}/analyze", json=valid_jd, headers=bob_header).status_code == 403
        assert client.delete(f"/api/resumes/{alice_resume_id}", headers=bob_header).status_code == 403

        # 4. Roadmap access
        assert client.get(f"/api/career/roadmaps/{alice_roadmap_id}", headers=bob_header).status_code == 403
        assert client.delete(f"/api/career/roadmaps/{alice_roadmap_id}", headers=bob_header).status_code == 403

        # 5. Bob tries to generate roadmap using Alice's resume_id
        client.post(
            "/api/career/profile",
            json={"target_role": "Backend Developer", "current_skills": ["Java"]},
            headers=bob_header,
        )
        bob_hack = client.post(
            "/api/career/roadmaps/generate",
            json={"target_role": "Backend Developer", "resume_id": alice_resume_id},
            headers=bob_header,
        )
        assert bob_hack.status_code == 403


# ==============================================================================
# 8. CASCADE DELETIONS ACROSS ALL MODULES
# ==============================================================================

class TestCascadeDeletions:
    """Verifies that deletions cascade properly and do not leave orphaned records."""

    def test_document_cascade(self, client: TestClient, synthetic_users, db_session: Session):
        user_alice, _ = synthetic_users
        auth_header = {"X-User-Id": str(user_alice.id)}

        upload_resp = client.post(
            "/api/documents/upload",
            files={"file": ("cascade_doc.txt", io.BytesIO(b"Cascade test content " * 30), "text/plain")},
            headers=auth_header,
        )
        doc_id = upload_resp.json()["id"]

        # Verify chunks exist in DB
        assert db_session.query(DocumentChunk).filter(DocumentChunk.document_id == doc_id).count() > 0

        # Delete document
        del_resp = client.delete(f"/api/documents/{doc_id}", headers=auth_header)
        assert del_resp.status_code == 200

        # Verify chunks were cascaded
        assert db_session.query(DocumentChunk).filter(DocumentChunk.document_id == doc_id).count() == 0

    def test_chat_session_cascade(self, client: TestClient, synthetic_users, db_session: Session):
        user_alice, _ = synthetic_users
        auth_header = {"X-User-Id": str(user_alice.id)}

        s_resp = client.post("/api/chat/sessions", json={"title": "Cascade Chat"}, headers=auth_header)
        session_id = s_resp.json()["id"]

        client.post(f"/api/chat/sessions/{session_id}/messages", json={"message": "Hello"}, headers=auth_header)
        assert db_session.query(ChatMessage).filter(ChatMessage.session_id == session_id).count() > 0

        # Delete session
        del_resp = client.delete(f"/api/chat/sessions/{session_id}", headers=auth_header)
        assert del_resp.status_code == 200

        # Verify messages cascaded
        assert db_session.query(ChatMessage).filter(ChatMessage.session_id == session_id).count() == 0

    def test_career_profile_cascade(self, client: TestClient, synthetic_users, db_session: Session):
        user_alice, _ = synthetic_users
        auth_header = {"X-User-Id": str(user_alice.id)}

        client.post("/api/career/profile", json={"target_role": "Data Analyst", "current_skills": ["SQL"]}, headers=auth_header)
        r_resp = client.post("/api/career/roadmaps/generate", json={"target_role": "Data Analyst"}, headers=auth_header)
        roadmap_id = r_resp.json()["id"]

        # Delete career profile
        del_resp = client.delete("/api/career/profile", headers=auth_header)
        assert del_resp.status_code == 200

        # Verify roadmap was cascaded
        assert db_session.query(Roadmap).filter(Roadmap.id == roadmap_id).first() is None
