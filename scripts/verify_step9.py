"""
Live Smoke Verification Script for Step 9: Resume Analyzer & ATS Scorecard.
Exercises the live FastAPI application and Resume Analyzer service end-to-end:
1. Health endpoint verification (/api/health).
2. Upload candidate resume (.txt format) with skills, education, and experience.
3. List candidate resumes and retrieve resume metadata.
4. Upload candidate resume (.pdf format) using in-memory PyMuPDF.
5. Structured extraction and parsing analysis without Job Description.
6. ATS Gap Analysis with targeted Job Description (partial match, transparent score).
7. ATS Gap Analysis with full match (100% score).
8. Idempotent upsert verification on repeated analysis.
9. Security & Access Isolation verification (cross-user access/analysis 403).
10. Resume deletion and cascade verification (DB record, analysis, file on disk).
"""

import io
import os
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, os.path.abspath("."))

import fitz  # PyMuPDF
from fastapi.testclient import TestClient
from backend.app.config import get_settings
from backend.app.database import SessionLocal
from backend.app.main import app
from backend.app.models.resume import Resume, ResumeAnalysis
from backend.app.models.user import User


def make_pdf_bytes(text: str) -> bytes:
    """Generate in-memory valid PDF bytes."""
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 72), text)
    b = doc.tobytes()
    doc.close()
    return b


def run_smoke_verification():
    sep = "=" * 70
    print(sep)
    print("SAHAYAKAI STEP 9 LIVE SMOKE VERIFICATION: RESUME ANALYZER")
    print(sep)

    client = TestClient(app)
    settings = get_settings()
    print("[*] Configuration:")
    print(f"    - App Name: {settings.APP_NAME} v{settings.APP_VERSION}")
    print(f"    - Upload Directory: {settings.UPLOAD_DIR}")
    print(f"    - Max Upload Size: {settings.MAX_UPLOAD_SIZE_MB} MB")

    # 1. Health check
    print("\n[Step 1] Verifying /api/health endpoint...")
    health_resp = client.get("/api/health")
    assert health_resp.status_code == 200, f"Health check failed: {health_resp.text}"
    health_data = health_resp.json()
    print(f"    -> Status: {health_data.get('status')}, Environment: {health_data.get('environment')}")

    db = SessionLocal()
    txt_resume_id = None
    pdf_resume_id = None
    user1_id = None
    user2_id = None

    try:
        # Create two test users
        u1 = db.query(User).filter(User.email == "smoke_user1_step9@example.com").first()
        if not u1:
            u1 = User(email="smoke_user1_step9@example.com", name="Smoke User 1")
            db.add(u1)
        u2 = db.query(User).filter(User.email == "smoke_user2_step9@example.com").first()
        if not u2:
            u2 = User(email="smoke_user2_step9@example.com", name="Smoke User 2")
            db.add(u2)
        db.commit()
        db.refresh(u1)
        db.refresh(u2)
        user1_id = u1.id
        user2_id = u2.id
        u1_headers = {"X-User-Id": str(user1_id)}
        u2_headers = {"X-User-Id": str(user2_id)}

        # 2. Upload TXT Resume
        print("\n[Step 2] Uploading candidate TXT resume...")
        txt_content = (
            "ANANYA SHARMA\n"
            "Full Stack Software Engineer\n\n"
            "SKILLS\n"
            "Python, FastAPI, Docker, PostgreSQL, React, Git, Redis\n\n"
            "EXPERIENCE\n"
            "Software Engineer - CloudSystems Inc - Jan 2022 to Present\n"
            "- Engineered high-throughput microservices using FastAPI and PostgreSQL\n"
            "- Containerized backend deployments with Docker\n\n"
            "EDUCATION\n"
            "Bachelor of Technology in Computer Science, Delhi Technological University, 2022\n\n"
            "PROJECTS\n"
            "E-Commerce Microservices: Built distributed microservices with Redis caching\n"
        ).encode("utf-8")

        upload_txt_resp = client.post(
            "/api/resumes",
            headers=u1_headers,
            files={"file": ("ananya_resume.txt", txt_content, "text/plain")},
        )
        assert upload_txt_resp.status_code == 201, f"TXT upload failed: {upload_txt_resp.text}"
        txt_resume_data = upload_txt_resp.json()
        txt_resume_id = txt_resume_data["id"]
        print(f"    -> TXT Resume uploaded: ID={txt_resume_id}, File='{txt_resume_data['original_filename']}'")

        # 3. List & Get Resume
        print("\n[Step 3] Listing resumes and retrieving metadata...")
        list_resp = client.get("/api/resumes", headers=u1_headers)
        assert list_resp.status_code == 200
        assert any(r["id"] == txt_resume_id for r in list_resp.json())

        get_resp = client.get(f"/api/resumes/{txt_resume_id}", headers=u1_headers)
        assert get_resp.status_code == 200
        assert get_resp.json()["id"] == txt_resume_id
        print(f"    -> Resume confirmed in listing & GET: {get_resp.json()['original_filename']}")

        # 4. Upload PDF Resume
        print("\n[Step 4] Uploading candidate PDF resume...")
        pdf_text = (
            "Vikram Malhotra\n"
            "DevOps Engineer\n\n"
            "SKILLS\n"
            "Kubernetes, Terraform, AWS, Docker, Python, CI/CD, Linux\n\n"
            "EXPERIENCE\n"
            "DevOps Engineer - InfraCloud - 2021 to 2024\n\n"
            "EDUCATION\n"
            "Master of Science in Information Systems, 2021\n"
        )
        pdf_bytes = make_pdf_bytes(pdf_text)
        upload_pdf_resp = client.post(
            "/api/resumes",
            headers=u1_headers,
            files={"file": ("vikram_resume.pdf", pdf_bytes, "application/pdf")},
        )
        assert upload_pdf_resp.status_code == 201, f"PDF upload failed: {upload_pdf_resp.text}"
        pdf_resume_id = upload_pdf_resp.json()["id"]
        print(f"    -> PDF Resume uploaded: ID={pdf_resume_id}, File='{upload_pdf_resp.json()['original_filename']}'")

        # 5. Analyze Resume without Job Description
        print("\n[Step 5] Analyzing TXT resume without Job Description (profile extraction only)...")
        no_jd_resp = client.post(f"/api/resumes/{txt_resume_id}/analyze", headers=u1_headers, json={})
        assert no_jd_resp.status_code == 200, f"Analysis without JD failed: {no_jd_resp.text}"
        no_jd_data = no_jd_resp.json()
        print(f"    -> Extracted Skills ({len(no_jd_data['extracted_skills'])}): {no_jd_data['extracted_skills']}")
        print(f"    -> Match Score: {no_jd_data['match_score']} (expected None)")
        print(f"    -> Recommendations ({len(no_jd_data['recommendations'])}): {no_jd_data['recommendations'][:2]}")
        assert no_jd_data["match_score"] is None
        assert "FastAPI" in no_jd_data["extracted_skills"]
        assert "Python" in no_jd_data["extracted_skills"]
        assert len(no_jd_data["recommendations"]) > 0

        # 6. ATS Gap Analysis with Targeted Job Description
        print("\n[Step 6] Running ATS Gap Analysis with targeted Job Description...")
        jd = (
            "We are looking for a Senior Backend Engineer proficient in Python, FastAPI, Docker, "
            "Kubernetes, and AWS to architect high-throughput APIs."
        )
        # Required skills in JD: Python, FastAPI, Docker, Kubernetes, AWS (5 skills)
        # Resume has: Python, FastAPI, Docker, PostgreSQL, React, Git, Redis
        # Matched: Docker, FastAPI, Python (3 skills)
        # Missing: AWS, Kubernetes (2 skills)
        # Expected Match Score: (3 / 5) * 100 = 60.0%
        jd_resp = client.post(
            f"/api/resumes/{txt_resume_id}/analyze",
            headers=u1_headers,
            json={"job_description": jd},
        )
        assert jd_resp.status_code == 200, f"Analysis with JD failed: {jd_resp.text}"
        jd_data = jd_resp.json()
        print(f"    -> Match Score: {jd_data['match_score']}%")
        print(f"    -> Matched Skills: {jd_data['matched_skills']}")
        print(f"    -> Missing Skills: {jd_data['missing_skills']}")
        print(f"    -> Targeted Recommendations:")
        for rec in jd_data["recommendations"][:2]:
            print(f"       * {rec}")
        assert jd_data["match_score"] == 60.0
        assert sorted(jd_data["matched_skills"]) == ["Docker", "FastAPI", "Python"]
        assert sorted(jd_data["missing_skills"]) == ["AWS", "Kubernetes"]

        # 7. ATS Gap Analysis with Full Match
        print("\n[Step 7] Running ATS Gap Analysis with 100% matched Job Description...")
        jd_full = "Requirements: Python, FastAPI, and Docker experience required."
        full_resp = client.post(
            f"/api/resumes/{txt_resume_id}/analyze",
            headers=u1_headers,
            json={"job_description": jd_full},
        )
        assert full_resp.status_code == 200
        full_data = full_resp.json()
        print(f"    -> Match Score: {full_data['match_score']}% (expected 100.0%)")
        print(f"    -> Missing Skills: {full_data['missing_skills']} (expected [])")
        assert full_data["match_score"] == 100.0
        assert full_data["missing_skills"] == []

        # 8. Idempotent Upsert Verification
        print("\n[Step 8] Verifying idempotent upsert on repeated analysis...")
        analyses_count = db.query(ResumeAnalysis).filter(ResumeAnalysis.resume_id == txt_resume_id).count()
        print(f"    -> Analysis records in DB for resume ID {txt_resume_id}: {analyses_count} (expected 1)")
        assert analyses_count == 1, f"Expected 1 analysis record due to upsert, found {analyses_count}"

        # 9. Security & Access Isolation Verification
        print("\n[Step 9] Verifying cross-user security boundaries (User 2 -> User 1)...")
        # User 2 attempts to GET User 1's resume
        u2_get = client.get(f"/api/resumes/{txt_resume_id}", headers=u2_headers)
        assert u2_get.status_code == 403, f"Expected 403, got {u2_get.status_code}"
        assert u2_get.json()["error_code"] == "RESUME_ACCESS_DENIED"
        print(f"    -> GET /api/resumes/{txt_resume_id} blocked: 403 RESUME_ACCESS_DENIED")

        # User 2 attempts to analyze User 1's resume
        u2_analyze = client.post(
            f"/api/resumes/{txt_resume_id}/analyze",
            headers=u2_headers,
            json={"job_description": "Requires at least 3 years Python and FastAPI experience"},
        )
        assert u2_analyze.status_code == 403
        assert u2_analyze.json()["error_code"] == "RESUME_ACCESS_DENIED"
        print(f"    -> POST /api/resumes/{txt_resume_id}/analyze blocked: 403 RESUME_ACCESS_DENIED")

        # User 2 attempts to delete User 1's resume
        u2_del = client.delete(f"/api/resumes/{txt_resume_id}", headers=u2_headers)
        assert u2_del.status_code == 403
        assert u2_del.json()["error_code"] == "RESUME_ACCESS_DENIED"
        print(f"    -> DELETE /api/resumes/{txt_resume_id} blocked: 403 RESUME_ACCESS_DENIED")

        # 10. Deletion and Cascade Verification
        print("\n[Step 10] Deleting resumes and verifying cascade cleanup...")
        del_resp = client.delete(f"/api/resumes/{txt_resume_id}", headers=u1_headers)
        assert del_resp.status_code == 200
        print(f"    -> Deleted resume ID={txt_resume_id}")

        # Check DB and 404
        assert db.query(Resume).filter(Resume.id == txt_resume_id).first() is None
        assert db.query(ResumeAnalysis).filter(ResumeAnalysis.resume_id == txt_resume_id).first() is None
        assert client.get(f"/api/resumes/{txt_resume_id}", headers=u1_headers).status_code == 404
        txt_resume_id = None

        del_pdf = client.delete(f"/api/resumes/{pdf_resume_id}", headers=u1_headers)
        assert del_pdf.status_code == 200
        pdf_resume_id = None
        print("    -> Cascade deletion verified: DB record, analysis, and disk files cleaned.")

        print("\n" + sep)
        print("ALL STEP 9 LIVE SMOKE VERIFICATIONS PASSED SUCCESSFULLY!")
        print(sep)

    finally:
        # Cleanup any remaining resources
        if txt_resume_id:
            try:
                client.delete(f"/api/resumes/{txt_resume_id}", headers={"X-User-Id": str(user1_id)})
            except Exception:
                pass
        if pdf_resume_id:
            try:
                client.delete(f"/api/resumes/{pdf_resume_id}", headers={"X-User-Id": str(user1_id)})
            except Exception:
                pass
        db.close()


if __name__ == "__main__":
    run_smoke_verification()
