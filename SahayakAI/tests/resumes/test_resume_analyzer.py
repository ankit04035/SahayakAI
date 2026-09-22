"""
Comprehensive Automated Test Suite for Resume Analyzer (Step 9).
Covers:
- Group A: Resume Upload & Validation (valid txt/pdf, invalid types, size limits, sanitization, user mapping)
- Group B: Structured Resume Parsing (sections, education, experience, messy/plain text, edge cases)
- Group C: Skill Extraction & Normalization (aliases, boundaries, multi-word, case-insensitivity, deduplication)
- Group D: Job Description Matching & Gap Analysis (match score formula, matched/missing, zero skills, null JD)
- Group E: Recommendation Engine (missing skills advice, missing section guidance, quantifiable impact)
- Group F: Persistence & Idempotency (database records, upsert on re-analysis, cascade delete)
- Group G: Security & Access Isolation (cross-user access/analyze/delete 403, 404 not found)
- Group H: REST API Endpoints (POST /resumes, GET /resumes, GET /resumes/{id}, POST /resumes/{id}/analyze,
           GET /resumes/{id}/analyses, DELETE /resumes/{id})
"""

import io
from pathlib import Path
import fitz  # PyMuPDF
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.app.config import get_settings
from backend.app.database import SessionLocal
from backend.app.main import app
from backend.app.models.resume import Resume, ResumeAnalysis
from backend.app.models.user import User
from backend.app.nlp.resume_parser import (
    extract_education,
    extract_experience,
    parse_resume_sections,
    parse_structured_resume,
)
from backend.app.nlp.skill_extractor import (
    extract_skills,
    normalize_skill,
)
from backend.app.services.resume_exceptions import (
    ResumeAccessDeniedError,
    ResumeAnalysisNotFoundError,
    ResumeNotFoundError,
    ResumeProcessingError,
)
from backend.app.services.resume_service import (
    analyze_resume,
    create_resume_upload,
    delete_resume,
    extract_resume_text,
    generate_recommendations,
    get_analysis,
    get_analyses,
    get_resume,
    list_resumes,
)


# ==============================================================================
# FIXTURES
# ==============================================================================

@pytest.fixture
def db_session():
    """Provide a database session for testing with guaranteed cleanup."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client():
    """FastAPI TestClient for API endpoint verification."""
    return TestClient(app)


@pytest.fixture
def test_users(db_session: Session):
    """Create two test users to verify ownership isolation."""
    user1 = db_session.query(User).filter(User.email == "user1_resume@example.com").first()
    if not user1:
        user1 = User(email="user1_resume@example.com", name="Resume User 1")
        db_session.add(user1)

    user2 = db_session.query(User).filter(User.email == "user2_resume@example.com").first()
    if not user2:
        user2 = User(email="user2_resume@example.com", name="Resume User 2")
        db_session.add(user2)

    db_session.commit()
    db_session.refresh(user1)
    db_session.refresh(user2)

    yield user1, user2

    # Cleanup resumes and analyses created by these users
    resumes = db_session.query(Resume).filter(Resume.user_id.in_([user1.id, user2.id])).all()
    settings = get_settings()
    for r in resumes:
        p = Path(settings.UPLOAD_DIR) / "resumes" / r.stored_filename
        if p.exists():
            try:
                p.unlink()
            except Exception:
                pass
        db_session.delete(r)
    db_session.commit()


def make_sample_pdf_bytes(text: str) -> bytes:
    """Generate in-memory valid PDF bytes for testing."""
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 72), text)
    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


# ==============================================================================
# GROUP A: RESUME UPLOAD & VALIDATION
# ==============================================================================

class TestResumeUploadAndValidation:
    """Tests for resume upload, validation, sanitization, and storage."""

    def test_upload_valid_txt_resume(self, client: TestClient, test_users):
        user1, _ = test_users
        content = b"John Doe\nSoftware Engineer\nSkills: Python, FastAPI, Docker, PostgreSQL\nEducation: BS Computer Science\n"
        response = client.post(
            "/api/resumes",
            headers={"X-User-Id": str(user1.id)},
            files={"file": ("john_doe_resume.txt", content, "text/plain")},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["original_filename"] == "john_doe_resume.txt"
        assert data["file_type"] == ".txt"
        assert data["user_id"] == user1.id
        assert data["processing_status"] == "completed"
        assert "id" in data

    def test_upload_valid_pdf_resume(self, client: TestClient, test_users):
        user1, _ = test_users
        sample_text = (
            "Alice Smith\nSenior Developer\n"
            "Technical Skills: Python, Kubernetes, AWS, Terraform, Docker\n"
            "Education: Master of Science in Software Engineering, MIT, 2020\n"
            "Experience: Lead Engineer at CloudTech (2020-2023)\n"
        )
        pdf_bytes = make_sample_pdf_bytes(sample_text)

        response = client.post(
            "/api/resumes",
            headers={"X-User-Id": str(user1.id)},
            files={"file": ("alice_resume.pdf", pdf_bytes, "application/pdf")},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["original_filename"] == "alice_resume.pdf"
        assert data["file_type"] == ".pdf"
        assert data["user_id"] == user1.id
        assert data["file_size"] == len(pdf_bytes)

    def test_upload_invalid_extension(self, client: TestClient, test_users):
        user1, _ = test_users
        response = client.post(
            "/api/resumes",
            headers={"X-User-Id": str(user1.id)},
            files={"file": ("malware.exe", b"binary content", "application/octet-stream")},
        )
        assert response.status_code == 400
        data = response.json()
        assert data["error_code"] == "INVALID_FILE_TYPE"

    def test_upload_empty_file(self, client: TestClient, test_users):
        user1, _ = test_users
        response = client.post(
            "/api/resumes",
            headers={"X-User-Id": str(user1.id)},
            files={"file": ("empty.txt", b"", "text/plain")},
        )
        assert response.status_code == 400
        data = response.json()
        assert data["error_code"] == "EMPTY_FILE"

    def test_upload_filename_sanitization(self, client: TestClient, test_users):
        user1, _ = test_users
        content = b"Resume content\nSkills: Python, Git\n"
        response = client.post(
            "/api/resumes",
            headers={"X-User-Id": str(user1.id)},
            files={"file": ("../../etc/passwd_evil.txt", content, "text/plain")},
        )
        assert response.status_code == 201
        data = response.json()
        assert ".." not in data["original_filename"]
        assert "/" not in data["original_filename"]


# ==============================================================================
# GROUP B: STRUCTURED RESUME PARSING
# ==============================================================================

class TestStructuredResumeParsing:
    """Unit tests for section detection and entity parsing."""

    def test_parse_resume_sections_detected(self):
        text = (
            "Alex Mercer\n"
            "Summary: Passionate backend engineer.\n\n"
            "SKILLS\n"
            "Python, FastAPI, Redis, Docker\n\n"
            "EXPERIENCE\n"
            "Backend Engineer | TechNova | 2021 - Present\n"
            "- Designed scalable microservices handling 10k RPS\n\n"
            "EDUCATION\n"
            "B.Tech in Computer Science, Delhi University, 2021\n\n"
            "PROJECTS\n"
            "SahayakAI: Intelligent study and career assistant\n"
        )
        sections = parse_resume_sections(text)
        assert "skills" in sections
        assert "experience" in sections
        assert "education" in sections
        assert "projects" in sections
        assert "FastAPI" in sections["skills"]

    def test_extract_education_details(self):
        edu_text = (
            "EDUCATION\n"
            "Bachelor of Science in Computer Science, Stanford University, 2019\n"
            "Master of Science in Artificial Intelligence, Carnegie Mellon University, 2021\n"
        )
        entries = extract_education(edu_text)
        assert len(entries) >= 1
        found_degree = any("Bachelor of Science" in (e.get("degree") or "") or "Master of Science" in (e.get("degree") or "") for e in entries)
        assert found_degree

    def test_extract_experience_details(self):
        exp_text = (
            "EXPERIENCE\n"
            "Senior Backend Engineer at Stripe (2021 - 2024)\n"
            "- Architected payment routing engine\n"
            "Software Engineer at Google (2018 - 2021)\n"
        )
        entries = extract_experience(exp_text)
        assert len(entries) >= 1
        titles = [e.get("role") for e in entries if e.get("role")]
        assert any("Backend Engineer" in t or "Software Engineer" in t for t in titles)

    def test_parse_structured_resume_plain_text(self):
        freeform_text = (
            "Experienced programmer proficient in Python, React, PostgreSQL, and Docker. "
            "Graduated from MIT with a degree in EECS in 2020. Worked at Meta building feed ranking."
        )
        structured = parse_structured_resume(freeform_text)
        assert "skills" in structured
        assert "Python" in structured["skills"]
        assert "React" in structured["skills"]
        assert "PostgreSQL" in structured["skills"]

    def test_parse_structured_resume_empty(self):
        structured = parse_structured_resume("")
        assert structured["skills"] == []
        assert structured["education"] == []
        assert structured["experience"] == []


# ==============================================================================
# GROUP C: SKILL EXTRACTION & NORMALIZATION
# ==============================================================================

class TestSkillExtractionAndNormalization:
    """Unit tests for dictionary alias normalization and boundary-safe matching."""

    def test_skill_alias_normalization(self):
        assert normalize_skill("k8s") == "Kubernetes"
        assert normalize_skill("py") == "Python"
        assert normalize_skill("reactjs") == "React"
        assert normalize_skill("react.js") == "React"
        assert normalize_skill("ts") == "TypeScript"
        assert normalize_skill("postgres") == "PostgreSQL"
        assert normalize_skill("postgresql") == "PostgreSQL"
        assert normalize_skill("js") == "JavaScript"
        assert normalize_skill("golang") == "Go"

    def test_boundary_aware_matching(self):
        text_negative = "Good morning everyone. We are going to the category store."
        skills_neg = extract_skills(text_negative)
        assert "Go" not in skills_neg
        assert "C" not in skills_neg

        text_positive = "Skills: Go, Python, and C++."
        skills_pos = extract_skills(text_positive)
        assert "Go" in skills_pos
        assert "Python" in skills_pos
        assert "C++" in skills_pos

    def test_multi_word_skills(self):
        text = "Extensive experience in Machine Learning, Deep Learning, Natural Language Processing, and CI/CD."
        skills = extract_skills(text)
        assert "Machine Learning" in skills
        assert "Deep Learning" in skills
        assert "Natural Language Processing" in skills
        assert "CI/CD" in skills

    def test_case_insensitivity_and_deduplication(self):
        text = "python, PYTHON, Python, Py, PY, py"
        skills = extract_skills(text)
        assert skills == ["Python"]


# ==============================================================================
# GROUP D: JOB DESCRIPTION MATCHING & SCORING
# ==============================================================================

class TestJobDescriptionMatchingAndScoring:
    """Tests for ATS match score formula and gap analysis."""

    def test_partial_match_score(self, db_session: Session, test_users):
        user1, _ = test_users
        resume_content = b"Candidate Skills: Python, FastAPI, Docker, Git\n"
        resume = create_resume_upload(
            file_content=resume_content,
            original_filename="cand_partial.txt",
            db=db_session,
            user_id=user1.id,
        )

        jd = "Seeking a Senior Engineer with Python, FastAPI, Kubernetes, AWS, and Docker experience."
        analysis = analyze_resume(db=db_session, resume_id=resume.id, job_description=jd, user_id=user1.id)

        assert analysis.match_score == 60.0
        assert sorted(analysis.matched_skills) == ["Docker", "FastAPI", "Python"]
        assert sorted(analysis.missing_skills) == ["AWS", "Kubernetes"]

    def test_full_match_score(self, db_session: Session, test_users):
        user1, _ = test_users
        resume_content = b"Skills: Python, Docker, PostgreSQL, Redis\n"
        resume = create_resume_upload(
            file_content=resume_content,
            original_filename="cand_full.txt",
            db=db_session,
            user_id=user1.id,
        )
        jd = "Requirements: Python, Docker, Redis."
        analysis = analyze_resume(db=db_session, resume_id=resume.id, job_description=jd, user_id=user1.id)
        assert analysis.match_score == 100.0
        assert analysis.missing_skills == []

    def test_zero_match_score(self, db_session: Session, test_users):
        user1, _ = test_users
        resume_content = b"Skills: HTML, CSS, Figma\n"
        resume = create_resume_upload(
            file_content=resume_content,
            original_filename="cand_zero.txt",
            db=db_session,
            user_id=user1.id,
        )
        jd = "Requirements: Kubernetes, Rust, Golang."
        analysis = analyze_resume(db=db_session, resume_id=resume.id, job_description=jd, user_id=user1.id)
        assert analysis.match_score == 0.0
        assert analysis.matched_skills == []
        assert len(analysis.missing_skills) == 3

    def test_jd_without_technical_skills(self, db_session: Session, test_users):
        user1, _ = test_users
        resume_content = b"Skills: Python, FastAPI\n"
        resume = create_resume_upload(
            file_content=resume_content,
            original_filename="cand_noskills.txt",
            db=db_session,
            user_id=user1.id,
        )
        jd = "We are seeking an enthusiastic team player with strong interpersonal skills."
        analysis = analyze_resume(db=db_session, resume_id=resume.id, job_description=jd, user_id=user1.id)
        assert analysis.match_score == 100.0
        assert analysis.matched_skills == []
        assert analysis.missing_skills == []

    def test_analysis_without_jd(self, db_session: Session, test_users):
        user1, _ = test_users
        resume_content = b"Skills: Python, PyTorch, Docker\nEducation: BS in CS\n"
        resume = create_resume_upload(
            file_content=resume_content,
            original_filename="cand_no_jd.txt",
            db=db_session,
            user_id=user1.id,
        )
        analysis = analyze_resume(db=db_session, resume_id=resume.id, job_description=None, user_id=user1.id)
        assert analysis.match_score is None
        assert analysis.matched_skills == []
        assert analysis.missing_skills == []
        assert "Python" in analysis.extracted_skills
        assert len(analysis.recommendations) > 0


# ==============================================================================
# GROUP E: RECOMMENDATION ENGINE
# ==============================================================================

class TestRecommendationEngine:
    """Tests for traceable, constructive feedback generation."""

    def test_recommendations_reflect_missing_competencies(self):
        structured = {"skills": ["Python"], "education": [{"degree": "BS"}], "experience": [{"role": "Dev"}], "projects": ["Project 1"]}
        missing = ["Kubernetes", "Terraform"]
        recs = generate_recommendations(structured, missing, 50.0)

        assert any("Kubernetes" in r and "Terraform" in r for r in recs)
        assert any("Quantifiable" in r for r in recs)

    def test_recommendations_prompt_missing_sections(self):
        structured = {"skills": ["Python"], "education": [], "experience": [], "projects": []}
        recs = generate_recommendations(structured, [], 100.0)

        assert any("Education Section" in r for r in recs)
        assert any("Experience Section" in r for r in recs)
        assert any("Portfolio Projects" in r for r in recs)


# ==============================================================================
# GROUP F: PERSISTENCE & IDEMPOTENCY
# ==============================================================================

class TestPersistenceAndIdempotency:
    """Tests for DB persistence, idempotent re-analysis, and cascade deletion."""

    def test_reanalysis_upsert_idempotency(self, db_session: Session, test_users):
        user1, _ = test_users
        resume_content = b"Skills: Python, FastAPI\n"
        resume = create_resume_upload(
            file_content=resume_content,
            original_filename="cand_upsert.txt",
            db=db_session,
            user_id=user1.id,
        )

        analysis1 = analyze_resume(db=db_session, resume_id=resume.id, job_description="Requires Python", user_id=user1.id)
        first_id = analysis1.id
        assert analysis1.match_score == 100.0

        analysis2 = analyze_resume(db=db_session, resume_id=resume.id, job_description="Requires Python, Kubernetes", user_id=user1.id)
        assert analysis2.id == first_id
        assert analysis2.match_score == 50.0
        assert "Kubernetes" in analysis2.missing_skills

        all_analyses = db_session.query(ResumeAnalysis).filter(ResumeAnalysis.resume_id == resume.id).all()
        assert len(all_analyses) == 1

    def test_cascade_deletion(self, db_session: Session, test_users):
        user1, _ = test_users
        resume_content = b"Skills: Python, SQL\n"
        resume = create_resume_upload(
            file_content=resume_content,
            original_filename="cand_cascade.txt",
            db=db_session,
            user_id=user1.id,
        )
        analyze_resume(db=db_session, resume_id=resume.id, job_description="Requires Python", user_id=user1.id)

        settings = get_settings()
        stored_path = Path(settings.UPLOAD_DIR) / "resumes" / resume.stored_filename
        assert stored_path.exists()

        delete_resume(db=db_session, resume_id=resume.id, user_id=user1.id)

        assert db_session.query(Resume).filter(Resume.id == resume.id).first() is None
        assert db_session.query(ResumeAnalysis).filter(ResumeAnalysis.resume_id == resume.id).first() is None
        assert not stored_path.exists()


# ==============================================================================
# GROUP G: SECURITY & ACCESS ISOLATION
# ==============================================================================

class TestSecurityAndAccessIsolation:
    """Tests for multi-tenant pre-auth user boundaries and forbidden operations."""

    def test_cross_user_get_resume_forbidden(self, client: TestClient, db_session: Session, test_users):
        user1, user2 = test_users
        resume = create_resume_upload(
            file_content=b"User 1 confidential resume\nSkills: Python\n",
            original_filename="u1_res.txt",
            db=db_session,
            user_id=user1.id,
        )
        response = client.get(f"/api/resumes/{resume.id}", headers={"X-User-Id": str(user2.id)})
        assert response.status_code == 403
        data = response.json()
        assert data["error_code"] == "RESUME_ACCESS_DENIED"

    def test_cross_user_analyze_resume_forbidden(self, client: TestClient, db_session: Session, test_users):
        user1, user2 = test_users
        resume = create_resume_upload(
            file_content=b"User 1 resume\nSkills: Python\n",
            original_filename="u1_analyze.txt",
            db=db_session,
            user_id=user1.id,
        )
        response = client.post(
            f"/api/resumes/{resume.id}/analyze",
            headers={"X-User-Id": str(user2.id)},
            json={"job_description": "Requires Python"},
        )
        assert response.status_code == 403
        data = response.json()
        assert data["error_code"] == "RESUME_ACCESS_DENIED"

    def test_cross_user_delete_resume_forbidden(self, client: TestClient, db_session: Session, test_users):
        user1, user2 = test_users
        resume = create_resume_upload(
            file_content=b"User 1 resume\nSkills: Python\n",
            original_filename="u1_del.txt",
            db=db_session,
            user_id=user1.id,
        )
        response = client.delete(f"/api/resumes/{resume.id}", headers={"X-User-Id": str(user2.id)})
        assert response.status_code == 403
        data = response.json()
        assert data["error_code"] == "RESUME_ACCESS_DENIED"

    def test_get_nonexistent_resume(self, client: TestClient, test_users):
        user1, _ = test_users
        response = client.get("/api/resumes/999999", headers={"X-User-Id": str(user1.id)})
        assert response.status_code == 404
        assert response.json()["error_code"] == "RESUME_NOT_FOUND"

    def test_get_nonexistent_analysis(self, client: TestClient, db_session: Session, test_users):
        user1, _ = test_users
        resume = create_resume_upload(
            file_content=b"Skills: Python\n",
            original_filename="u1_no_analysis.txt",
            db=db_session,
            user_id=user1.id,
        )
        response = client.get(f"/api/resumes/{resume.id}/analyses/999999", headers={"X-User-Id": str(user1.id)})
        assert response.status_code == 404
        assert response.json()["error_code"] == "ANALYSIS_NOT_FOUND"


# ==============================================================================
# GROUP H: REST API ENDPOINTS END-TO-END
# ==============================================================================

class TestResumeApiEndToEnd:
    """End-to-end HTTP workflow tests for candidate resume lifecycle."""

    def test_full_resume_lifecycle(self, client: TestClient, test_users):
        user1, _ = test_users
        headers = {"X-User-Id": str(user1.id)}

        # 1. Upload Resume
        content = (
            "Jane Doe\n"
            "Technical Skills: Python, FastAPI, Docker, PostgreSQL\n"
            "Education: Bachelor of Science in Computer Science, 2021\n"
            "Experience: Backend Developer at ACME, 2021-2024\n"
        ).encode("utf-8")

        upload_res = client.post(
            "/api/resumes",
            headers=headers,
            files={"file": ("jane_resume.txt", content, "text/plain")},
        )
        assert upload_res.status_code == 201
        resume_id = upload_res.json()["id"]

        # 2. List Resumes
        list_res = client.get("/api/resumes", headers=headers)
        assert list_res.status_code == 200
        resumes_list = list_res.json()
        assert any(r["id"] == resume_id for r in resumes_list)

        # 3. Get Specific Resume
        get_res = client.get(f"/api/resumes/{resume_id}", headers=headers)
        assert get_res.status_code == 200
        assert get_res.json()["original_filename"] == "jane_resume.txt"

        # 4. Analyze Resume with Job Description
        jd_payload = {
            "job_description": "We are seeking a Python engineer experienced with FastAPI, Docker, and Kubernetes."
        }
        analyze_res = client.post(f"/api/resumes/{resume_id}/analyze", headers=headers, json=jd_payload)
        assert analyze_res.status_code == 200
        analysis_data = analyze_res.json()
        analysis_id = analysis_data["id"]
        assert analysis_data["match_score"] == 75.0
        assert "Kubernetes" in analysis_data["missing_skills"]
        assert "Python" in analysis_data["matched_skills"]
        assert len(analysis_data["recommendations"]) > 0

        # 5. List Analyses
        analyses_res = client.get(f"/api/resumes/{resume_id}/analyses", headers=headers)
        assert analyses_res.status_code == 200
        assert len(analyses_res.json()) >= 1

        # 6. Get Specific Analysis
        single_analysis_res = client.get(f"/api/resumes/{resume_id}/analyses/{analysis_id}", headers=headers)
        assert single_analysis_res.status_code == 200
        assert single_analysis_res.json()["id"] == analysis_id

        # 7. Delete Resume
        del_res = client.delete(f"/api/resumes/{resume_id}", headers=headers)
        assert del_res.status_code == 200
        assert del_res.json()["message"] == "Resume deleted successfully"

        # 8. Verify 404 after deletion
        verify_del = client.get(f"/api/resumes/{resume_id}", headers=headers)
        assert verify_del.status_code == 404
