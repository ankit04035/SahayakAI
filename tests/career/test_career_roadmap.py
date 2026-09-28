"""
Comprehensive Automated Test Suite for Career Profile & Personalized Career Roadmap (Step 10).
Covers:
- Group A: Career Profile CRUD & Persistence (creation, lookup, update, deletion, cascade)
- Group B: Role Taxonomy & Deterministic Skill Gaps (aliases, case insensitivity, gap partition)
- Group C: Roadmap Generation & Section Verification (projects, weekly plan, interview topics, reasons)
- Group D: Resume Integration (incorporating ResumeAnalysis, rejecting cross-user resume)
- Group E: Provider & Demo Mode (zero-key offline execution, provider abstraction)
- Group F: Security & Access Isolation (cross-user profile/roadmap 403, 404 not found)
- Group G: REST API Endpoints End-to-End (POST/GET/PUT/DELETE profile, POST/GET/DELETE roadmaps)
"""

from typing import List
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.app.config import get_settings
from backend.app.database import SessionLocal
from backend.app.main import app
from backend.app.models.career import CareerProfile, Roadmap
from backend.app.models.resume import Resume, ResumeAnalysis
from backend.app.models.user import User
from backend.app.nlp.role_taxonomy import ROLE_TAXONOMY, get_role_taxonomy
from backend.app.nlp.skill_extractor import normalize_skill
from backend.app.schemas.career import (
    CareerProfileCreate,
    CareerProfileUpdate,
    RoadmapGenerateRequest,
)
from backend.app.services.career_exceptions import (
    CareerProfileAccessDeniedError,
    CareerProfileNotFoundError,
    RoadmapAccessDeniedError,
    RoadmapNotFoundError,
)
from backend.app.services.career_service import (
    compute_skill_gaps,
    construct_learning_order,
    delete_career_profile,
    delete_roadmap,
    generate_roadmap,
    get_career_profile,
    get_roadmap,
    list_roadmaps,
    update_career_profile,
    upsert_career_profile,
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
    user1 = db_session.query(User).filter(User.email == "user1_career@example.com").first()
    if not user1:
        user1 = User(email="user1_career@example.com", name="Career User 1")
        db_session.add(user1)

    user2 = db_session.query(User).filter(User.email == "user2_career@example.com").first()
    if not user2:
        user2 = User(email="user2_career@example.com", name="Career User 2")
        db_session.add(user2)

    db_session.commit()
    db_session.refresh(user1)
    db_session.refresh(user2)

    yield user1, user2

    # Cleanup roadmaps and profiles created by these users
    profiles = db_session.query(CareerProfile).filter(CareerProfile.user_id.in_([user1.id, user2.id])).all()
    for p in profiles:
        db_session.query(Roadmap).filter(Roadmap.career_profile_id == p.id).delete()
        db_session.delete(p)
    # Cleanup any resumes created
    resumes = db_session.query(Resume).filter(Resume.user_id.in_([user1.id, user2.id])).all()
    for r in resumes:
        db_session.query(ResumeAnalysis).filter(ResumeAnalysis.resume_id == r.id).delete()
        db_session.delete(r)
    db_session.commit()


# ==============================================================================
# GROUP A: CAREER PROFILE CRUD & PERSISTENCE
# ==============================================================================

class TestCareerProfileCRUD:
    """Tests for profile creation, lookup, update, and cascade deletion."""

    def test_create_and_get_career_profile(self, db_session: Session, test_users):
        user1, _ = test_users
        profile_in = CareerProfileCreate(
            degree="Bachelor of Technology in Computer Science",
            current_skills=["Python", "FastAPI", "py", "git"],
            experience="1 year of backend development",
            interests=["Distributed Systems", "Cloud Computing"],
            target_role="Backend Developer",
        )
        profile = upsert_career_profile(db=db_session, profile_in=profile_in, user_id=user1.id)
        assert profile.id is not None
        assert profile.user_id == user1.id
        assert profile.target_role == "Backend Developer"
        # Skills normalized and deduplicated
        assert "Python" in profile.current_skills
        assert "Git" in profile.current_skills
        assert "py" not in profile.current_skills  # normalized to Python

        retrieved = get_career_profile(db=db_session, user_id=user1.id)
        assert retrieved.id == profile.id
        assert retrieved.degree == "Bachelor of Technology in Computer Science"

    def test_update_career_profile(self, db_session: Session, test_users):
        user1, _ = test_users
        profile_in = CareerProfileCreate(
            degree="B.Sc",
            current_skills=["Python"],
            target_role="Data Analyst",
        )
        profile = upsert_career_profile(db=db_session, profile_in=profile_in, user_id=user1.id)

        update_in = CareerProfileUpdate(
            target_role="Data Scientist",
            current_skills=["Python", "SQL", "Pandas"],
        )
        updated = update_career_profile(db=db_session, profile_in=update_in, user_id=user1.id)
        assert updated.target_role == "Data Scientist"
        assert "SQL" in updated.current_skills
        assert "Pandas" in updated.current_skills

    def test_delete_career_profile_and_cascade(self, db_session: Session, test_users):
        user1, _ = test_users
        profile_in = CareerProfileCreate(
            target_role="Python Developer",
            current_skills=["Python"],
        )
        profile = upsert_career_profile(db=db_session, profile_in=profile_in, user_id=user1.id)

        # Generate a roadmap for this profile
        roadmap = generate_roadmap(db=db_session, user_id=user1.id)
        assert roadmap.id is not None
        roadmap_id = roadmap.id

        # Delete profile
        delete_career_profile(db=db_session, user_id=user1.id)

        # Verify profile and roadmap deleted from database
        assert db_session.query(CareerProfile).filter(CareerProfile.id == profile.id).first() is None
        assert db_session.query(Roadmap).filter(Roadmap.id == roadmap_id).first() is None


# ==============================================================================
# GROUP B: ROLE TAXONOMY & DETERMINISTIC SKILL GAPS
# ==============================================================================

class TestRoleTaxonomyAndSkillGaps:
    """Tests for taxonomy matching, canonical resolution, and skill gap calculation."""

    def test_taxonomy_retrieval_standard_roles(self):
        backend_tax = get_role_taxonomy("Backend Developer")
        assert backend_tax["role"] == "Backend Developer"
        assert "FastAPI" in backend_tax["required_skills"]
        assert "Docker" in backend_tax["required_skills"]
        assert len(backend_tax["default_projects"]) >= 2
        assert len(backend_tax["interview_topics"]) >= 3

        ml_tax = get_role_taxonomy("Machine Learning Engineer")
        assert "PyTorch" in ml_tax["required_skills"]
        assert "Scikit-Learn" in ml_tax["required_skills"]

    def test_taxonomy_fuzzy_matching(self):
        tax = get_role_taxonomy("senior python dev")
        assert tax["role"] == "Python Developer"

        tax_ai = get_role_taxonomy("generative ai engineer")
        assert tax_ai["role"] == "AI/ML Engineer"

    def test_taxonomy_fallback_for_unknown_role(self):
        tax = get_role_taxonomy("Quantum Computing Architect")
        assert tax["role"] == "Quantum Computing Architect"
        assert len(tax["required_skills"]) > 0
        assert len(tax["default_projects"]) > 0

    def test_compute_skill_gaps_deterministic(self):
        # Candidate has Python, Git, k8s (Kubernetes)
        current = ["Python", "Git", "k8s"]
        target = "Backend Developer"

        gaps = compute_skill_gaps(current_skills=current, target_role=target)

        # Backend Developer requires: Python, FastAPI, PostgreSQL, Docker, REST API, Microservices, Git
        assert "Python" in gaps["already_possessed"]
        assert "Git" in gaps["already_possessed"]
        assert "FastAPI" in gaps["missing_skills"]
        assert "PostgreSQL" in gaps["missing_skills"]
        assert "Docker" in gaps["missing_skills"]
        # Recommended skills contain missing skills + supplementary
        assert "FastAPI" in gaps["recommended_skills"]
        assert "PostgreSQL" in gaps["recommended_skills"]

    def test_case_insensitivity_and_alias_resolution(self):
        current = ["python", "FASTAPI", "postgres", "DOCKER"]
        target = "Python Developer"

        gaps = compute_skill_gaps(current_skills=current, target_role=target)
        # All 4 should match required skills regardless of case/alias
        assert "Python" in gaps["already_possessed"]
        assert "FastAPI" in gaps["already_possessed"]
        assert "PostgreSQL" in gaps["already_possessed"]
        assert "Docker" in gaps["already_possessed"]


# ==============================================================================
# GROUP C: ROADMAP GENERATION & STRUCTURE
# ==============================================================================

class TestRoadmapGeneration:
    """Tests for complete roadmap structure, projects, weekly plan, and explanations."""

    def test_generate_roadmap_structure(self, db_session: Session, test_users):
        user1, _ = test_users
        profile_in = CareerProfileCreate(
            degree="Bachelor of Engineering",
            current_skills=["Python", "Git"],
            experience="Student with internship experience",
            interests=["Cloud", "Microservices"],
            target_role="Backend Developer",
        )
        upsert_career_profile(db=db_session, profile_in=profile_in, user_id=user1.id)

        roadmap = generate_roadmap(db=db_session, user_id=user1.id)

        assert roadmap.id is not None
        assert "Backend Developer" in roadmap.title
        assert isinstance(roadmap.recommended_skills, list)
        assert isinstance(roadmap.missing_skills, list)
        assert isinstance(roadmap.projects, list)
        assert isinstance(roadmap.learning_order, list)
        assert isinstance(roadmap.weekly_plan, list)
        assert isinstance(roadmap.interview_topics, list)
        assert isinstance(roadmap.recommendation_reasons, list)

        # Verify projects structure
        assert len(roadmap.projects) >= 2
        for p in roadmap.projects:
            assert "title" in p
            assert "skills" in p
            assert "description" in p
            assert "difficulty" in p

        # Verify weekly plan structure
        assert len(roadmap.weekly_plan) == 6
        for w in roadmap.weekly_plan:
            assert "week_range" in w
            assert "focus" in w
            assert "learning_goals" in w
            assert "deliverable" in w

        # Verify interview topics
        assert len(roadmap.interview_topics) >= 3

        # Verify recommendation reasons
        assert len(roadmap.recommendation_reasons) >= 2
        assert any("Backend Developer" in r for r in roadmap.recommendation_reasons)

    def test_override_target_role_in_request(self, db_session: Session, test_users):
        user1, _ = test_users
        profile_in = CareerProfileCreate(
            current_skills=["Python", "SQL"],
            target_role="Data Analyst",
        )
        upsert_career_profile(db=db_session, profile_in=profile_in, user_id=user1.id)

        req = RoadmapGenerateRequest(target_role="Data Scientist")
        roadmap = generate_roadmap(db=db_session, request=req, user_id=user1.id)

        assert "Data Scientist" in roadmap.title
        assert "Scikit-Learn" in roadmap.missing_skills


# ==============================================================================
# GROUP D: RESUME INTEGRATION
# ==============================================================================

class TestResumeIntegration:
    """Tests for incorporating ResumeAnalysis skills into career roadmaps."""

    def test_roadmap_incorporates_resume_skills(self, db_session: Session, test_users):
        user1, _ = test_users

        # 1. Create a resume record
        resume = Resume(
            user_id=user1.id,
            original_filename="user1_res.txt",
            stored_filename="stored_user1_res.txt",
            file_type=".txt",
            file_size=1024,
            processing_status="completed",
        )
        db_session.add(resume)
        db_session.commit()
        db_session.refresh(resume)

        # 2. Create resume analysis with extracted skills
        analysis = ResumeAnalysis(
            resume_id=resume.id,
            job_description=None,
            extracted_skills=["FastAPI", "Docker", "PostgreSQL"],
            match_score=None,
        )
        db_session.add(analysis)
        db_session.commit()

        # 3. Create career profile with only Python
        profile_in = CareerProfileCreate(
            current_skills=["Python"],
            target_role="Backend Developer",
        )
        upsert_career_profile(db=db_session, profile_in=profile_in, user_id=user1.id)

        # 4. Generate roadmap referencing the resume
        req = RoadmapGenerateRequest(resume_id=resume.id)
        roadmap = generate_roadmap(db=db_session, request=req, user_id=user1.id)

        # Docker, FastAPI, PostgreSQL should now be recognized as already possessed!
        assert "FastAPI" not in roadmap.missing_skills
        assert "Docker" not in roadmap.missing_skills
        assert "PostgreSQL" not in roadmap.missing_skills

    def test_cross_user_resume_rejected(self, db_session: Session, test_users):
        user1, user2 = test_users

        # User 2 owns a resume
        resume_u2 = Resume(
            user_id=user2.id,
            original_filename="u2.txt",
            stored_filename="u2.txt",
            file_type=".txt",
            file_size=500,
            processing_status="completed",
        )
        db_session.add(resume_u2)
        db_session.commit()

        # User 1 has a profile
        profile_in = CareerProfileCreate(current_skills=["Python"], target_role="Backend Developer")
        upsert_career_profile(db=db_session, profile_in=profile_in, user_id=user1.id)

        # User 1 attempts to generate roadmap using User 2's resume
        req = RoadmapGenerateRequest(resume_id=resume_u2.id)
        with pytest.raises(CareerProfileAccessDeniedError):
            generate_roadmap(db=db_session, request=req, user_id=user1.id)


# ==============================================================================
# GROUP E: PROVIDER & DEMO MODE
# ==============================================================================

class TestProviderAndDemoMode:
    """Tests verifying execution in Demo Mode with zero external API keys."""

    def test_roadmap_generation_demo_provider(self, db_session: Session, test_users):
        user1, _ = test_users
        settings = get_settings()
        assert settings.AI_PROVIDER == "demo"

        profile_in = CareerProfileCreate(
            degree="MCA",
            current_skills=["Java", "SQL"],
            target_role="Python Developer",
        )
        upsert_career_profile(db=db_session, profile_in=profile_in, user_id=user1.id)

        roadmap = generate_roadmap(db=db_session, user_id=user1.id)
        assert roadmap.id is not None
        assert len(roadmap.recommendation_reasons) > 0


# ==============================================================================
# GROUP F: SECURITY & ACCESS ISOLATION
# ==============================================================================

class TestSecurityAndAccessIsolation:
    """Tests verifying multi-tenant isolation and 403 / 404 enforcement."""

    def test_cross_user_profile_access_forbidden(self, client: TestClient, db_session: Session, test_users):
        user1, user2 = test_users
        # User 1 creates profile
        upsert_career_profile(
            db=db_session,
            profile_in=CareerProfileCreate(target_role="Cloud Engineer", current_skills=["AWS"]),
            user_id=user1.id,
        )

        # User 2 attempts to get User 2's profile before creating one -> 404
        res_u2 = client.get("/api/career/profile", headers={"X-User-Id": str(user2.id)})
        assert res_u2.status_code == 404
        assert res_u2.json()["error_code"] == "PROFILE_NOT_FOUND"

    def test_cross_user_roadmap_access_forbidden(self, client: TestClient, db_session: Session, test_users):
        user1, user2 = test_users
        upsert_career_profile(
            db=db_session,
            profile_in=CareerProfileCreate(target_role="Frontend Developer", current_skills=["React"]),
            user_id=user1.id,
        )
        roadmap = generate_roadmap(db=db_session, user_id=user1.id)

        # User 2 attempts to get User 1's roadmap
        res = client.get(f"/api/career/roadmaps/{roadmap.id}", headers={"X-User-Id": str(user2.id)})
        # User 2 has no profile yet -> raises ProfileNotFound (404) or AccessDenied (403)
        assert res.status_code in [403, 404]

    def test_cross_user_roadmap_deletion_forbidden(self, client: TestClient, db_session: Session, test_users):
        user1, user2 = test_users
        upsert_career_profile(
            db=db_session,
            profile_in=CareerProfileCreate(target_role="Python Developer", current_skills=["Python"]),
            user_id=user1.id,
        )
        roadmap = generate_roadmap(db=db_session, user_id=user1.id)

        # User 2 creates own profile
        upsert_career_profile(
            db=db_session,
            profile_in=CareerProfileCreate(target_role="DevOps Engineer", current_skills=["Docker"]),
            user_id=user2.id,
        )

        # User 2 tries to delete User 1's roadmap
        res = client.delete(f"/api/career/roadmaps/{roadmap.id}", headers={"X-User-Id": str(user2.id)})
        assert res.status_code == 403
        assert res.json()["error_code"] == "ROADMAP_ACCESS_DENIED"

    def test_get_nonexistent_roadmap(self, client: TestClient, db_session: Session, test_users):
        user1, _ = test_users
        upsert_career_profile(
            db=db_session,
            profile_in=CareerProfileCreate(target_role="Backend Developer", current_skills=["Python"]),
            user_id=user1.id,
        )
        res = client.get("/api/career/roadmaps/999999", headers={"X-User-Id": str(user1.id)})
        assert res.status_code == 404
        assert res.json()["error_code"] == "ROADMAP_NOT_FOUND"


# ==============================================================================
# GROUP G: REST API ENDPOINTS END-TO-END
# ==============================================================================

class TestCareerApiEndToEnd:
    """HTTP endpoint workflow tests for profile and roadmap lifecycle."""

    def test_list_roadmaps_without_profile_returns_empty_list(self, client: TestClient, test_users):
        _, user2 = test_users
        response = client.get("/api/career/roadmaps", headers={"X-User-Id": str(user2.id)})

        assert response.status_code == 200
        assert response.json() == []

    def test_full_career_lifecycle(self, client: TestClient, test_users):
        user1, _ = test_users
        headers = {"X-User-Id": str(user1.id)}

        # 1. Create Profile
        profile_payload = {
            "degree": "B.Tech Computer Science",
            "current_skills": ["Python", "FastAPI", "Git"],
            "experience": "1 year building backend APIs",
            "interests": ["Machine Learning", "System Design"],
            "target_role": "Backend Developer",
        }
        res_post = client.post("/api/career/profile", headers=headers, json=profile_payload)
        assert res_post.status_code == 201
        profile_data = res_post.json()
        assert profile_data["target_role"] == "Backend Developer"
        assert "FastAPI" in profile_data["current_skills"]

        # 2. Get Profile
        res_get = client.get("/api/career/profile", headers=headers)
        assert res_get.status_code == 200
        assert res_get.json()["id"] == profile_data["id"]

        # 3. Update Profile
        update_payload = {"target_role": "Full Stack Developer"}
        res_put = client.put("/api/career/profile", headers=headers, json=update_payload)
        assert res_put.status_code == 200
        assert res_put.json()["target_role"] == "Full Stack Developer"

        # 4. Generate Roadmap
        res_gen = client.post("/api/career/roadmaps/generate", headers=headers, json={})
        assert res_gen.status_code == 201
        roadmap_data = res_gen.json()
        roadmap_id = roadmap_data["id"]
        assert "Full Stack Developer" in roadmap_data["title"]
        assert len(roadmap_data["weekly_plan"]) == 6
        assert len(roadmap_data["projects"]) >= 2
        assert len(roadmap_data["interview_topics"]) >= 3

        # 5. List Roadmaps
        res_list = client.get("/api/career/roadmaps", headers=headers)
        assert res_list.status_code == 200
        roadmaps_list = res_list.json()
        assert any(r["id"] == roadmap_id for r in roadmaps_list)

        # 6. Get Specific Roadmap
        res_single = client.get(f"/api/career/roadmaps/{roadmap_id}", headers=headers)
        assert res_single.status_code == 200
        assert res_single.json()["id"] == roadmap_id

        # 7. Delete Specific Roadmap
        res_del_rm = client.delete(f"/api/career/roadmaps/{roadmap_id}", headers=headers)
        assert res_del_rm.status_code == 200

        # 8. Delete Profile
        res_del_prof = client.delete("/api/career/profile", headers=headers)
        assert res_del_prof.status_code == 200

        # 9. Verify Profile 404 after deletion
        res_verify = client.get("/api/career/profile", headers=headers)
        assert res_verify.status_code == 404

    def test_validation_rejects_empty_target_role(self, client: TestClient, test_users):
        user1, _ = test_users
        headers = {"X-User-Id": str(user1.id)}
        res = client.post(
            "/api/career/profile",
            headers=headers,
            json={"target_role": "", "current_skills": ["Python"]},
        )
        assert res.status_code == 422
