"""
STEP 11 Verification Script: Synthetic End-to-End User Journey.
Exercises Steps A through P:
- STEP A: Synthetic user creation
- STEP B: Upload synthetic study document
- STEP C: Process and embed document
- STEP D: Create document-grounded chat session
- STEP E: Ask grounded question about document
- STEP F: Verify grounded response with citations
- STEP G: Ask unrelated out-of-context question
- STEP H: Verify insufficient-evidence behavior
- STEP I: Upload synthetic candidate resume
- STEP J: Analyze resume against synthetic job description
- STEP K: Verify ATS match score and skill gaps
- STEP L: Create candidate CareerProfile
- STEP M: Generate personalized Career Roadmap referencing resume
- STEP N: Verify all roadmap sections (title, skills, projects, weekly plan, interview topics, reasons)
- STEP O: Verify cross-user access rejection (HTTP 403)
- STEP P: Verify full cleanup and resource deletion
"""

import io
import os
import sys

# Ensure repository root is on sys.path
sys.path.insert(0, os.getcwd())

from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.database import SessionLocal
from backend.app.models.user import User
from backend.app.models.document import Document, DocumentChunk
from backend.app.models.chat import ChatSession, ChatMessage
from backend.app.models.resume import Resume, ResumeAnalysis
from backend.app.models.career import CareerProfile, Roadmap


def run_verification():
    print("=" * 70)
    print("SAHAYAKAI STEP 11: FULL BACKEND INTEGRATION VERIFICATION")
    print("=" * 70)

    client = TestClient(app)
    db = SessionLocal()

    try:
        # ------------------------------------------------------------------
        # STEP A: Create Synthetic Users
        # ------------------------------------------------------------------
        print("\n[STEP A] Creating synthetic test users...")
        user_alice = db.query(User).filter(User.email == "synthetic_journey_alice@example.com").first()
        if not user_alice:
            user_alice = User(email="synthetic_journey_alice@example.com", name="Synthetic Alice Journey")
            db.add(user_alice)

        user_bob = db.query(User).filter(User.email == "synthetic_journey_bob@example.com").first()
        if not user_bob:
            user_bob = User(email="synthetic_journey_bob@example.com", name="Synthetic Bob Journey")
            db.add(user_bob)

        db.commit()
        db.refresh(user_alice)
        db.refresh(user_bob)

        alice_header = {"X-User-Id": str(user_alice.id)}
        bob_header = {"X-User-Id": str(user_bob.id)}
        print(f"  -> Alice ID: {user_alice.id}, Bob ID: {user_bob.id}")
        print("  [PASS] STEP A completed.")

        # ------------------------------------------------------------------
        # STEP B: Upload Synthetic Study Document
        # ------------------------------------------------------------------
        print("\n[STEP B] Uploading synthetic study document...")
        doc_content = (
            "Distributed Systems and Microservices Architecture Overview:\\n"
            "Microservices architecture structures an application as a collection of loosely coupled services.\\n"
            "FastAPI provides asynchronous request handling, automatic OpenAPI schema generation, and dependency injection.\\n"
            "Vector databases and sentence embeddings allow semantic search by converting text chunks into dense numeric vectors."
        ).encode("utf-8")

        upload_resp = client.post(
            "/api/documents/upload",
            files={"file": ("systems_architecture.txt", io.BytesIO(doc_content), "text/plain")},
            data={"title": "Systems Architecture Guide", "auto_embed": "true"},
            headers=alice_header,
        )
        assert upload_resp.status_code == 201, f"Document upload failed: {upload_resp.text}"
        doc_data = upload_resp.json()
        doc_id = doc_data["id"]
        print(f"  -> Uploaded Document ID: {doc_id}, Chunks: {doc_data['chunk_count']}")
        print("  [PASS] STEP B completed.")

        # ------------------------------------------------------------------
        # STEP C: Process and Embed Document
        # ------------------------------------------------------------------
        print("\n[STEP C] Verifying document processing and chunk embeddings...")
        chunks_resp = client.get(f"/api/documents/{doc_id}/chunks", headers=alice_header)
        assert chunks_resp.status_code == 200, f"Chunks retrieval failed: {chunks_resp.text}"
        chunks = chunks_resp.json()
        assert len(chunks) > 0, "No chunks generated!"
        print(f"  -> Retrieved {len(chunks)} chunks with persisted embeddings.")
        print("  [PASS] STEP C completed.")

        # ------------------------------------------------------------------
        # STEP D: Create Document-Grounded Chat Session
        # ------------------------------------------------------------------
        print("\n[STEP D] Creating document-grounded chat session...")
        session_resp = client.post(
            "/api/chat/sessions",
            json={"title": "Architecture Study Session", "document_id": doc_id},
            headers=alice_header,
        )
        assert session_resp.status_code == 201, f"Session creation failed: {session_resp.text}"
        session_data = session_resp.json()
        session_id = session_data["id"]
        print(f"  -> Created Chat Session ID: {session_id}, Document ID: {session_data['document_id']}")
        print("  [PASS] STEP D completed.")

        # ------------------------------------------------------------------
        # STEP E: Ask Question About Document
        # ------------------------------------------------------------------
        print("\n[STEP E] Asking grounded question about document...")
        msg_payload = {"message": "How does microservices architecture structure an application?"}
        msg_resp = client.post(
            f"/api/chat/sessions/{session_id}/messages",
            json=msg_payload,
            headers=alice_header,
        )
        assert msg_resp.status_code == 200, f"Message send failed: {msg_resp.text}"
        ans_data = msg_resp.json()
        print("  [PASS] STEP E completed.")

        # ------------------------------------------------------------------
        # STEP F: Verify Grounded Answer and Sources
        # ------------------------------------------------------------------
        print("\n[STEP F] Verifying grounded response and citations...")
        assert ans_data["grounded"] is True, "Expected response to be grounded!"
        assert len(ans_data["sources"]) > 0, "Expected at least one cited source reference!"
        content = ans_data["assistant_message"]["content"]
        assert len(content) > 0, "Assistant message was empty!"
        print(f"  -> Grounded: {ans_data['grounded']}, Citations: {len(ans_data['sources'])}")
        print(f"  -> Answer snippet: {content[:100]}...")
        print("  [PASS] STEP F completed.")

        # ------------------------------------------------------------------
        # STEP G: Ask Unrelated Question
        # ------------------------------------------------------------------
        print("\n[STEP G] Asking unrelated out-of-context question...")
        ooc_payload = {"message": "What is the boiling point of ethanol in Fahrenheit?"}
        ooc_resp = client.post(
            f"/api/chat/sessions/{session_id}/messages",
            json=ooc_payload,
            headers=alice_header,
        )
        assert ooc_resp.status_code == 200, f"OOC message failed: {ooc_resp.text}"
        ooc_data = ooc_resp.json()
        print("  [PASS] STEP G completed.")

        # ------------------------------------------------------------------
        # STEP H: Verify Insufficient Evidence Behavior
        # ------------------------------------------------------------------
        print("\n[STEP H] Verifying insufficient-evidence behavior...")
        assert ooc_data["insufficient_evidence"] is True or ooc_data["grounded"] is False, "Expected ungrounded fallback!"
        print(f"  -> Handled safely: insufficient_evidence={ooc_data['insufficient_evidence']}, grounded={ooc_data['grounded']}")
        print("  [PASS] STEP H completed.")

        # ------------------------------------------------------------------
        # STEP I: Upload Synthetic Resume
        # ------------------------------------------------------------------
        print("\n[STEP I] Uploading synthetic resume...")
        resume_content = (
            "Alice Developer\\n"
            "Email: alice@example.com | Phone: 9876543210\\n\\n"
            "EDUCATION\\n"
            "B.Tech Computer Science, 2023\\n\\n"
            "SKILLS\\n"
            "Python, FastAPI, Docker, SQL, PostgreSQL, Git, Linux\\n\\n"
            "EXPERIENCE\\n"
            "Backend Engineer at CloudCorp (2023 - Present)\\n"
            "- Designed microservice APIs with Python and FastAPI\\n"
            "- Deployed containers with Docker\\n"
        ).encode("utf-8")

        res_upload = client.post(
            "/api/resumes",
            files={"file": ("alice_cv.txt", io.BytesIO(resume_content), "text/plain")},
            headers=alice_header,
        )
        assert res_upload.status_code == 201, f"Resume upload failed: {res_upload.text}"
        resume_data = res_upload.json()
        resume_id = resume_data["id"]
        print(f"  -> Uploaded Resume ID: {resume_id}")
        print("  [PASS] STEP I completed.")

        # ------------------------------------------------------------------
        # STEP J: Analyze Resume Against Synthetic Job Description
        # ------------------------------------------------------------------
        print("\n[STEP J] Analyzing resume against synthetic Job Description...")
        jd_text = (
            "Senior Backend Engineer\\n"
            "Required Skills: Python, FastAPI, Docker, Kubernetes, AWS, PostgreSQL, Redis."
        )
        analyze_resp = client.post(
            f"/api/resumes/{resume_id}/analyze",
            json={"job_description": jd_text},
            headers=alice_header,
        )
        assert analyze_resp.status_code == 200, f"Analysis failed: {analyze_resp.text}"
        analysis_data = analyze_resp.json()
        print("  [PASS] STEP J completed.")

        # ------------------------------------------------------------------
        # STEP K: Verify ATS Match Score and Skill Gaps
        # ------------------------------------------------------------------
        print("\n[STEP K] Verifying ATS match score and skill gaps...")
        assert 0.0 <= analysis_data["match_score"] <= 100.0, "Invalid match score!"
        assert len(analysis_data["matched_skills"]) > 0, "No matched skills found!"
        assert len(analysis_data["missing_skills"]) > 0, "No missing skills found!"
        assert len(analysis_data["recommendations"]) > 0, "No recommendations generated!"
        print(f"  -> ATS Match Score: {analysis_data['match_score']}%")
        print(f"  -> Matched Skills: {analysis_data['matched_skills']}")
        print(f"  -> Missing Skills: {analysis_data['missing_skills']}")
        print(f"  -> Recommendations: {len(analysis_data['recommendations'])}")
        print("  [PASS] STEP K completed.")

        # ------------------------------------------------------------------
        # STEP L: Create Career Profile
        # ------------------------------------------------------------------
        print("\n[STEP L] Creating CareerProfile...")
        profile_payload = {
            "degree": "B.Tech Computer Science",
            "target_role": "Backend Developer",
            "current_skills": ["Python", "Git", "SQL"],
            "experience": "1 year building backend services.",
            "interests": ["Microservices", "Cloud Architecture"],
        }
        prof_resp = client.post("/api/career/profile", json=profile_payload, headers=alice_header)
        assert prof_resp.status_code in [200, 201], f"Profile upsert failed: {prof_resp.text}"
        prof_data = prof_resp.json()
        print(f"  -> Career Profile ID: {prof_data['id']}, Target: {prof_data['target_role']}")
        print("  [PASS] STEP L completed.")

        # ------------------------------------------------------------------
        # STEP M: Generate Personalized Career Roadmap
        # ------------------------------------------------------------------
        print("\n[STEP M] Generating personalized Career Roadmap referencing resume...")
        roadmap_payload = {
            "target_role": "Backend Developer",
            "resume_id": resume_id,
        }
        road_resp = client.post("/api/career/roadmaps/generate", json=roadmap_payload, headers=alice_header)
        assert road_resp.status_code == 201, f"Roadmap generation failed: {road_resp.text}"
        roadmap_data = road_resp.json()
        roadmap_id = roadmap_data["id"]
        print(f"  -> Generated Roadmap ID: {roadmap_id}")
        print("  [PASS] STEP M completed.")

        # ------------------------------------------------------------------
        # STEP N: Verify All Roadmap Sections
        # ------------------------------------------------------------------
        print("\n[STEP N] Verifying roadmap contents and sections...")
        assert "Backend Developer" in roadmap_data["title"], "Missing target role in title"
        assert len(roadmap_data["recommended_skills"]) > 0, "Missing recommended skills"
        assert len(roadmap_data["missing_skills"]) > 0, "Missing missing skills"
        assert len(roadmap_data["projects"]) > 0, "Missing project recommendations"
        assert len(roadmap_data["learning_order"]) > 0, "Missing learning order"
        assert len(roadmap_data["weekly_plan"]) > 0, "Missing weekly plan"
        assert len(roadmap_data["interview_topics"]) > 0, "Missing interview topics"
        assert len(roadmap_data["recommendation_reasons"]) > 0, "Missing recommendation reasons"
        print("  -> Roadmap verified: title, skills, projects, weekly plan, interview topics, reasons present.")
        print("  [PASS] STEP N completed.")

        # ------------------------------------------------------------------
        # STEP O: Verify Cross-User Access Rejection (HTTP 403)
        # ------------------------------------------------------------------
        print("\n[STEP O] Verifying cross-user access rejection (HTTP 403)...")
        # Bob tries accessing Alice's Document
        assert client.get(f"/api/documents/{doc_id}", headers=bob_header).status_code == 403
        assert client.delete(f"/api/documents/{doc_id}", headers=bob_header).status_code == 403
        # Bob tries accessing Alice's Chat Session
        assert client.get(f"/api/chat/sessions/{session_id}", headers=bob_header).status_code == 403
        assert client.delete(f"/api/chat/sessions/{session_id}", headers=bob_header).status_code == 403
        # Bob tries accessing Alice's Resume
        assert client.get(f"/api/resumes/{resume_id}", headers=bob_header).status_code == 403
        assert client.delete(f"/api/resumes/{resume_id}", headers=bob_header).status_code == 403
        # Bob tries accessing Alice's Roadmap
        assert client.get(f"/api/career/roadmaps/{roadmap_id}", headers=bob_header).status_code == 403
        assert client.delete(f"/api/career/roadmaps/{roadmap_id}", headers=bob_header).status_code == 403
        print("  -> Cross-user operations on all 4 modules strictly rejected with HTTP 403 Forbidden.")
        print("  [PASS] STEP O completed.")

        # ------------------------------------------------------------------
        # STEP P: Verify Cleanup and Resource Deletion
        # ------------------------------------------------------------------
        print("\n[STEP P] Performing full cleanup and verifying deletion...")
        # 1. Delete Roadmap
        del_road = client.delete(f"/api/career/roadmaps/{roadmap_id}", headers=alice_header)
        assert del_road.status_code == 200
        # 2. Delete Career Profile
        del_prof = client.delete("/api/career/profile", headers=alice_header)
        assert del_prof.status_code == 200
        # 3. Delete Resume
        del_res = client.delete(f"/api/resumes/{resume_id}", headers=alice_header)
        assert del_res.status_code == 200
        # 4. Delete Chat Session
        del_sess = client.delete(f"/api/chat/sessions/{session_id}", headers=alice_header)
        assert del_sess.status_code == 200
        # 5. Delete Document
        del_doc = client.delete(f"/api/documents/{doc_id}", headers=alice_header)
        assert del_doc.status_code == 200

        # Verify DB records are gone
        assert db.query(Roadmap).filter(Roadmap.id == roadmap_id).first() is None
        assert db.query(CareerProfile).filter(CareerProfile.user_id == user_alice.id).first() is None
        assert db.query(Resume).filter(Resume.id == resume_id).first() is None
        assert db.query(ChatSession).filter(ChatSession.id == session_id).first() is None
        assert db.query(Document).filter(Document.id == doc_id).first() is None

        # Clean up test users
        db.delete(user_alice)
        db.delete(user_bob)
        db.commit()

        print("  -> All test resources successfully deleted and verified.")
        print("  [PASS] STEP P completed.")

        print("\n" + "=" * 70)
        print("ALL STEPS A THROUGH P VERIFIED SUCCESSFULLY! 100% PASS.")
        print("=" * 70)
        return True

    finally:
        db.close()


if __name__ == "__main__":
    success = run_verification()
    sys.exit(0 if success else 1)
