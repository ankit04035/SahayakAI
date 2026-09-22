"""
Live Smoke Verification Script for Step 10: Career Profile & Personalized Career Roadmap.
Exercises the live FastAPI application and Career Service end-to-end:
1. Health endpoint verification (/api/health).
2. Create CareerProfile with skills, degree, experience, and target role.
3. Retrieve CareerProfile and verify serialized state.
4. Update CareerProfile fields and verify patch persistence.
5. Generate personalized Career Roadmap in Demo Mode (zero-key).
6. Verify all required roadmap sections:
   - title
   - recommended_skills
   - missing_skills
   - projects
   - learning_order
   - weekly_plan
   - interview_topics
   - recommendation_reasons
7. Verify missing skills against target role taxonomy.
8. Verify recommended skills structure.
9. Verify structured portfolio projects.
10. Verify 12-week plan milestones.
11. Verify high-yield interview topics.
12. Retrieve persisted roadmap by ID and from roadmap listing.
13. Security & Access Isolation verification (cross-user access/deletion 403).
14. Roadmap deletion and profile deletion.
15. Verify database and state cleanup.
"""

import os
import sys

# Add project root to sys.path
sys.path.insert(0, os.path.abspath("."))

from fastapi.testclient import TestClient
from backend.app.config import get_settings
from backend.app.database import SessionLocal
from backend.app.main import app
from backend.app.models.career import CareerProfile, Roadmap
from backend.app.models.user import User


def run_smoke_verification():
    sep = "=" * 70
    print(sep)
    print("SAHAYAKAI STEP 10 LIVE SMOKE VERIFICATION: CAREER PROFILE & ROADMAP")
    print(sep)

    client = TestClient(app)
    settings = get_settings()
    print("[*] Configuration:")
    print(f"    - App Name: {settings.APP_NAME} v{settings.APP_VERSION}")
    print(f"    - AI Provider: {settings.AI_PROVIDER}")

    # 1. Health check
    print("\n[Step 1] Verifying /api/health endpoint...")
    health_resp = client.get("/api/health")
    assert health_resp.status_code == 200, f"Health check failed: {health_resp.text}"
    health_data = health_resp.json()
    print(f"    -> Status: {health_data.get('status')}")

    db = SessionLocal()
    user1_id = None
    user2_id = None
    created_roadmap_id = None

    try:
        # Create two test users
        u1 = db.query(User).filter(User.email == "smoke_user1_step10@example.com").first()
        if not u1:
            u1 = User(email="smoke_user1_step10@example.com", name="Smoke Career User 1")
            db.add(u1)
        u2 = db.query(User).filter(User.email == "smoke_user2_step10@example.com").first()
        if not u2:
            u2 = User(email="smoke_user2_step10@example.com", name="Smoke Career User 2")
            db.add(u2)
        db.commit()
        db.refresh(u1)
        db.refresh(u2)
        user1_id = u1.id
        user2_id = u2.id
        u1_headers = {"X-User-Id": str(user1_id)}
        u2_headers = {"X-User-Id": str(user2_id)}

        # Clean existing test profiles
        for uid in [user1_id, user2_id]:
            existing_prof = db.query(CareerProfile).filter(CareerProfile.user_id == uid).first()
            if existing_prof:
                db.query(Roadmap).filter(Roadmap.career_profile_id == existing_prof.id).delete()
                db.delete(existing_prof)
        db.commit()

        # 2. Create CareerProfile
        print("\n[Step 2] Creating candidate CareerProfile...")
        profile_payload = {
            "degree": "B.Tech in Computer Science and Engineering",
            "current_skills": ["Python", "FastAPI", "git", "py"],
            "experience": "1 year building backend REST APIs and microservices",
            "interests": ["Distributed Systems", "Cloud Infrastructure"],
            "target_role": "Backend Developer",
        }
        create_resp = client.post("/api/career/profile", headers=u1_headers, json=profile_payload)
        assert create_resp.status_code == 201, f"Create profile failed: {create_resp.text}"
        profile_data = create_resp.json()
        print(f"    -> CareerProfile created: ID={profile_data['id']}, Target Role='{profile_data['target_role']}'")
        print(f"    -> Normalized Skills: {profile_data['current_skills']}")
        assert "Python" in profile_data["current_skills"]
        assert "FastAPI" in profile_data["current_skills"]
        assert "Git" in profile_data["current_skills"]
        assert "py" not in profile_data["current_skills"]  # Normalized to Python

        # 3. Retrieve CareerProfile
        print("\n[Step 3] Retrieving CareerProfile via GET...")
        get_resp = client.get("/api/career/profile", headers=u1_headers)
        assert get_resp.status_code == 200
        assert get_resp.json()["id"] == profile_data["id"]
        print(f"    -> Retrieved profile confirmed: user_id={get_resp.json()['user_id']}")

        # 4. Update CareerProfile
        print("\n[Step 4] Updating CareerProfile via PUT...")
        update_payload = {
            "interests": ["Distributed Systems", "Cloud Infrastructure", "Kubernetes"],
            "current_skills": ["Python", "FastAPI", "Git", "Docker"],
        }
        put_resp = client.put("/api/career/profile", headers=u1_headers, json=update_payload)
        assert put_resp.status_code == 200
        assert "Docker" in put_resp.json()["current_skills"]
        print(f"    -> Updated skills: {put_resp.json()['current_skills']}")

        # 5. Generate Roadmap in Demo Mode
        print("\n[Step 5] Generating personalized Career Roadmap in Demo Mode...")
        gen_resp = client.post("/api/career/roadmaps/generate", headers=u1_headers, json={})
        assert gen_resp.status_code == 201, f"Generate roadmap failed: {gen_resp.text}"
        roadmap_data = gen_resp.json()
        created_roadmap_id = roadmap_data["id"]
        print(f"    -> Roadmap generated: ID={created_roadmap_id}, Title='{roadmap_data['title']}'")

        # 6. Verify required roadmap sections
        print("\n[Step 6] Verifying presence of all 8 required roadmap sections...")
        required_fields = [
            "title", "recommended_skills", "missing_skills", "projects",
            "learning_order", "weekly_plan", "interview_topics", "recommendation_reasons"
        ]
        for field in required_fields:
            assert field in roadmap_data, f"Missing field: {field}"
            assert roadmap_data[field] is not None, f"Field is None: {field}"
            print(f"    -> Section '{field}': Present (count/len: {len(roadmap_data[field])})")

        # 7. Verify missing skills
        print("\n[Step 7] Auditing missing skills against Backend Developer taxonomy...")
        print(f"    -> Missing Skills: {roadmap_data['missing_skills']}")
        # Backend Developer requires: Python, FastAPI, PostgreSQL, Docker, REST API, Microservices, Git
        # Candidate has: Python, FastAPI, Git, Docker
        # Missing should include: PostgreSQL, REST API, Microservices
        assert "PostgreSQL" in roadmap_data["missing_skills"]
        assert "Microservices" in roadmap_data["missing_skills"]
        assert "Python" not in roadmap_data["missing_skills"]

        # 8. Verify recommended skills
        print("\n[Step 8] Verifying recommended skills...")
        print(f"    -> Recommended Skills: {roadmap_data['recommended_skills']}")
        assert len(roadmap_data["recommended_skills"]) >= len(roadmap_data["missing_skills"])

        # 9. Verify projects
        print("\n[Step 9] Auditing portfolio project recommendations...")
        projects = roadmap_data["projects"]
        assert len(projects) >= 2
        for i, p in enumerate(projects):
            print(f"    -> Project {i+1}: '{p['title']}' [{p['difficulty']}]")
            print(f"       Skills: {p['skills']}")
            print(f"       Description: {p['description'][:80]}...")
            assert "title" in p and "skills" in p and "description" in p and "difficulty" in p

        # 10. Verify weekly plan
        print("\n[Step 10] Auditing weekly progression schedule...")
        weekly_plan = roadmap_data["weekly_plan"]
        assert len(weekly_plan) == 6  # 12 weeks divided into 6 bi-weekly milestones
        for wp in weekly_plan:
            print(f"    -> {wp['week_range']}: {wp['focus']}")
            assert "week_range" in wp and "focus" in wp and "learning_goals" in wp and "deliverable" in wp

        # 11. Verify interview topics
        print("\n[Step 11] Auditing technical interview topics...")
        interview_topics = roadmap_data["interview_topics"]
        assert len(interview_topics) >= 3
        for topic in interview_topics[:3]:
            print(f"    -> Topic: {topic}")

        # 12. Retrieve persisted roadmap
        print("\n[Step 12] Retrieving persisted roadmap by ID and list...")
        get_rm_resp = client.get(f"/api/career/roadmaps/{created_roadmap_id}", headers=u1_headers)
        assert get_rm_resp.status_code == 200
        assert get_rm_resp.json()["id"] == created_roadmap_id

        list_rm_resp = client.get("/api/career/roadmaps", headers=u1_headers)
        assert list_rm_resp.status_code == 200
        assert any(r["id"] == created_roadmap_id for r in list_rm_resp.json())
        print(f"    -> Confirmed roadmap persistence and retrieval (Total roadmaps: {len(list_rm_resp.json())})")

        # 13. Security & Access Isolation
        print("\n[Step 13] Verifying multi-tenant security boundaries (User 2 -> User 1)...")
        # User 2 attempts to get User 1's roadmap
        u2_get = client.get(f"/api/career/roadmaps/{created_roadmap_id}", headers=u2_headers)
        assert u2_get.status_code in [403, 404]
        print(f"    -> GET /api/career/roadmaps/{created_roadmap_id} by User 2 blocked: status {u2_get.status_code}")

        # User 2 creates profile
        client.post(
            "/api/career/profile",
            headers=u2_headers,
            json={"target_role": "Data Analyst", "current_skills": ["SQL"]},
        )
        # Now User 2 tries to delete User 1's roadmap
        u2_del = client.delete(f"/api/career/roadmaps/{created_roadmap_id}", headers=u2_headers)
        assert u2_del.status_code == 403
        assert u2_del.json()["error_code"] == "ROADMAP_ACCESS_DENIED"
        print(f"    -> DELETE /api/career/roadmaps/{created_roadmap_id} by User 2 blocked: 403 ROADMAP_ACCESS_DENIED")

        # 14. Deletion and Cleanup
        print("\n[Step 14] Deleting roadmap and profile...")
        del_rm = client.delete(f"/api/career/roadmaps/{created_roadmap_id}", headers=u1_headers)
        assert del_rm.status_code == 200
        print(f"    -> Deleted roadmap ID={created_roadmap_id}")

        del_prof = client.delete("/api/career/profile", headers=u1_headers)
        assert del_prof.status_code == 200
        print("    -> Deleted User 1 career profile")

        # 15. Verify 404 after cleanup
        verify_404 = client.get("/api/career/profile", headers=u1_headers)
        assert verify_404.status_code == 404
        print("    -> Cleanup verified: GET /api/career/profile returns 404 PROFILE_NOT_FOUND")

        print("\n" + sep)
        print("ALL STEP 10 LIVE SMOKE VERIFICATIONS PASSED SUCCESSFULLY!")
        print(sep)

    finally:
        # Final cleanup
        for uid in [user1_id, user2_id]:
            if uid:
                p = db.query(CareerProfile).filter(CareerProfile.user_id == uid).first()
                if p:
                    db.query(Roadmap).filter(Roadmap.career_profile_id == p.id).delete()
                    db.delete(p)
        db.commit()
        db.close()


if __name__ == "__main__":
    run_smoke_verification()
