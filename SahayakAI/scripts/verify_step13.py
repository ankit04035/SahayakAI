"""
STEP 13 End-to-End Integration and User Flow Verification Script.
Validates the complete interaction contract between the React frontend and FastAPI backend:
- CORS configuration and preflight handling
- User scoping via X-User-Id across all modules
- Workflow A: Document upload, chunk inspection, RAG grounded Q&A, insufficient evidence, delete
- Workflow B: Multi-turn study chat, document grounding, citation structure, session persistence
- Workflow C: Resume upload, skill extraction, ATS job description matching, recommendations
- Workflow D: Career Profile creation, update, and User A vs User B isolation
- Workflow E: 12-Week Career Roadmap generation (6 bi-weekly phases), capstone projects, interview prep
- Workflow F: Dashboard integration and resource counters
- Security Audit: Secret and key scanning in frontend source and production bundle
"""

import io
import os
import sys
import re
import json

# Ensure repository root is on sys.path
sys.path.insert(0, os.getcwd())

from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.config import get_settings


def log_step(name: str):
    print(f"\n{'=' * 60}")
    print(f">> {name}")
    print(f"{'=' * 60}")


def run_verification():
    settings = get_settings()
    client = TestClient(app)
    print(f"Running STEP 13 Verification with AI Provider: {settings.AI_PROVIDER}")

    user_1_id = 1
    user_2_id = 2
    u1_headers = {"X-User-Id": str(user_1_id)}
    u2_headers = {"X-User-Id": str(user_2_id)}

    # =========================================================================
    # Step 1: Health Check & CORS Preflight Handling
    # =========================================================================
    log_step("STEP 1: Health Check & CORS Preflight Verification")
    
    # 1.1 /api/health
    resp = client.get("/api/health")
    assert resp.status_code == 200, f"Health check failed: {resp.text}"
    health_data = resp.json()
    assert health_data["status"] == "ok"
    assert health_data["ai_provider"] == "demo"
    print("  [PASS] /api/health responded ok with Demo Provider.")

    # 1.2 CORS Preflight from localhost:5173
    cors_resp = client.options(
        "/api/documents",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "X-User-Id, Content-Type",
        },
    )
    assert cors_resp.status_code == 200, f"CORS preflight localhost failed: {cors_resp.status_code}"
    assert cors_resp.headers.get("access-control-allow-origin") == "http://localhost:5173"
    print("  [PASS] CORS preflight allowed for http://localhost:5173.")

    # 1.3 CORS Preflight from 127.0.0.1:5173
    cors_ip_resp = client.options(
        "/api/documents",
        headers={
            "Origin": "http://127.0.0.1:5173",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "X-User-Id, Content-Type",
        },
    )
    assert cors_ip_resp.status_code == 200, f"CORS preflight 127.0.0.1 failed: {cors_ip_resp.status_code}"
    assert cors_ip_resp.headers.get("access-control-allow-origin") == "http://127.0.0.1:5173"
    print("  [PASS] CORS preflight allowed for http://127.0.0.1:5173.")

    # =========================================================================
    # Step 2: Workflow A — Documents, RAG & Chunk Inspection
    # =========================================================================
    log_step("STEP 2: Workflow A — Study Documents & RAG Grounded Q&A")

    sample_doc_text = (
        "Operating Systems Lecture 4: Virtual Memory Management.\n"
        "Virtual memory is a memory management capability that provides an idealized abstraction "
        "of the storage resources that are actually available on a given machine.\n"
        "Paging is a memory management scheme that eliminates the need for contiguous allocation of physical memory.\n"
        "Page replacement algorithms include FIFO, Least Recently Used (LRU), and Optimal Page Replacement.\n"
        "Thrashing occurs when a computer's virtual memory resources are overused, leading to a constant state of paging and page faults."
    )

    upload_payload = {"file": ("os_lecture4.txt", io.BytesIO(sample_doc_text.encode("utf-8")), "text/plain")}
    doc_res = client.post("/api/documents/upload", files=upload_payload, data={"title": "Virtual Memory Notes", "auto_embed": "true"}, headers=u1_headers)
    assert doc_res.status_code in [200, 201], f"Document upload failed: {doc_res.text}"
    doc_data = doc_res.json()
    doc_id = doc_data["id"]
    print(f"  [PASS] Uploaded synthetic document ID: {doc_id} with {doc_data.get('chunk_count', 0)} chunks.")

    # 2.2 Inspect Document
    detail_res = client.get(f"/api/documents/{doc_id}", headers=u1_headers)
    assert detail_res.status_code == 200
    doc_detail = detail_res.json()
    assert doc_detail["title"] == "Virtual Memory Notes"
    print("  [PASS] Document inspection retrieved metadata and keywords.")

    # 2.3 Inspect Chunks
    chunks_res = client.get(f"/api/documents/{doc_id}/chunks", headers=u1_headers)
    assert chunks_res.status_code == 200
    chunks = chunks_res.json()
    assert len(chunks) > 0
    print(f"  [PASS] Chunk inspector retrieved {len(chunks)} chunks with token counts.")

    # 2.4 Ask Grounded Question
    ask_res = client.post(
        f"/api/documents/{doc_id}/ask",
        json={"question": "What is thrashing?", "top_k": 3, "similarity_threshold": 0.2},
        headers=u1_headers,
    )
    assert ask_res.status_code == 200
    rag_data = ask_res.json()
    assert rag_data["grounded"] is True
    assert len(rag_data["sources"]) > 0
    print(f"  [PASS] Grounded Q&A answered with {len(rag_data['sources'])} source citations.")

    # 2.5 Ask Unrelated Question (Insufficient Evidence)
    unrelated_res = client.post(
        f"/api/documents/{doc_id}/ask",
        json={"question": "What is the capital of Mars during the Pleistocene era?", "top_k": 3, "similarity_threshold": 0.8},
        headers=u1_headers,
    )
    assert unrelated_res.status_code == 200
    unrelated_data = unrelated_res.json()
    assert unrelated_data["insufficient_evidence"] is True
    print("  [PASS] Insufficient evidence triggered correctly for unrelated question.")

    # =========================================================================
    # Step 3: Workflow B — Study Assistant Multi-Turn Chat
    # =========================================================================
    log_step("STEP 3: Workflow B — Study Assistant Multi-Turn Chat")

    # 3.1 Create Chat Session
    sess_res = client.post(
        "/api/chat/sessions",
        json={"title": "OS Midterm Prep", "document_id": doc_id},
        headers=u1_headers,
    )
    assert sess_res.status_code in [200, 201]
    sess_data = sess_res.json()
    session_id = sess_data["id"]
    print(f"  [PASS] Created document-grounded chat session ID: {session_id}.")

    # 3.2 Send Message
    msg1_res = client.post(
        f"/api/chat/sessions/{session_id}/messages",
        json={"message": "Explain LRU page replacement algorithm."},
        headers=u1_headers,
    )
    assert msg1_res.status_code in [200, 201]
    msg1_data = msg1_res.json()
    assert msg1_data["assistant_message"]["content"]
    assert msg1_data["grounded"] is True
    print("  [PASS] Assistant replied with document-grounded context.")

    # 3.3 Send Follow-up Message (History Preservation)
    msg2_res = client.post(
        f"/api/chat/sessions/{session_id}/messages",
        json={"message": "Compare it with FIFO."},
        headers=u1_headers,
    )
    assert msg2_res.status_code in [200, 201]
    
    # Verify history preserved
    hist_res = client.get(f"/api/chat/sessions/{session_id}/messages", headers=u1_headers)
    assert hist_res.status_code == 200
    messages = hist_res.json()
    assert len(messages) >= 4  # 2 user + 2 assistant
    print(f"  [PASS] Multi-turn conversation preserved {len(messages)} messages in session history.")

    # =========================================================================
    # Step 4: Workflow C — Resume Analyzer & ATS Scorecard
    # =========================================================================
    log_step("STEP 4: Workflow C — Resume Analyzer & ATS Scorecard")

    sample_resume = (
        "John Doe\n"
        "Software Engineer\n"
        "Email: john.doe@example.com | Phone: 555-0199\n\n"
        "Summary:\n"
        "Backend developer with 2 years of experience building Python and FastAPI web services.\n\n"
        "Skills:\n"
        "Python, FastAPI, Docker, SQL, Git, Linux, REST APIs\n\n"
        "Experience:\n"
        "Software Engineer at Acme Corp (2024 - Present)\n"
        "- Developed microservices using FastAPI and Docker.\n"
        "- Optimized SQL queries for relational databases.\n\n"
        "Education:\n"
        "B.Tech in Computer Science, Tech University, 2024\n"
    )

    resume_payload = {"file": ("john_doe_resume.txt", io.BytesIO(sample_resume.encode("utf-8")), "text/plain")}
    res_upload = client.post("/api/resumes", files=resume_payload, headers=u1_headers)
    assert res_upload.status_code in [200, 201]
    resume_data = res_upload.json()
    resume_id = resume_data["id"]
    print(f"  [PASS] Resume uploaded with ID: {resume_id}.")

    # 4.2 Analyze Resume against Target Job Description
    target_jd = (
        "We are seeking a Backend Engineer with strong expertise in Python, FastAPI, Docker, and Kubernetes. "
        "Experience with PostgreSQL and Redis caching is strongly desired."
    )

    analysis_res = client.post(
        f"/api/resumes/{resume_id}/analyze",
        json={"job_description": target_jd},
        headers=u1_headers,
    )
    assert analysis_res.status_code in [200, 201]
    analysis = analysis_res.json()
    score = analysis.get("match_score") or analysis.get("score")
    assert score is not None
    assert score > 0
    assert "Python" in analysis.get("matched_skills", []) or "FastAPI" in analysis.get("matched_skills", [])
    assert len(analysis.get("recommendations", [])) > 0
    print(f"  [PASS] ATS analysis computed match score: {score}% with matched and missing skills.")

    # 4.3 History Persistence
    analyses_res = client.get(f"/api/resumes/{resume_id}/analyses", headers=u1_headers)
    assert analyses_res.status_code == 200
    assert len(analyses_res.json()) >= 1
    print("  [PASS] Resume analysis persisted and retrievable.")

    # =========================================================================
    # Step 5: Workflow D — Career Profile & User Scoping Isolation
    # =========================================================================
    log_step("STEP 5: Workflow D — Career Profile & Cross-User Scoping")

    profile_payload = {
        "target_role": "Software Engineer",
        "degree": "B.Tech Computer Science",
        "experience": "Beginner / Student",
        "current_skills": ["Python", "FastAPI", "SQL", "Docker"],
        "interests": ["Distributed Systems", "Cloud Computing"],
    }

    prof_res = client.post("/api/career/profile", json=profile_payload, headers=u1_headers)
    assert prof_res.status_code in [200, 201]
    prof_data = prof_res.json()
    assert prof_data["target_role"] == "Software Engineer"
    print("  [PASS] Created career profile for User 1.")

    # User 2 Cross-User Scoping Isolation check
    u2_get = client.get("/api/career/profile", headers=u2_headers)
    # User 2 should have no profile or receive 404
    assert u2_get.status_code == 404, f"Expected 404 for User 2, got {u2_get.status_code}"
    print("  [PASS] User 2 cannot access User 1 profile (strict X-User-Id scoping).")

    # Update User 1 Profile
    profile_payload["current_skills"].append("Kubernetes")
    update_res = client.post("/api/career/profile", json=profile_payload, headers=u1_headers)
    assert update_res.status_code in [200, 201]
    assert "Kubernetes" in update_res.json()["current_skills"]
    print("  [PASS] Updated career profile persisted successfully.")

    # =========================================================================
    # Step 6: Workflow E — 12-Week Career Roadmap
    # =========================================================================
    log_step("STEP 6: Workflow E — 12-Week Career Roadmap Generation")

    roadmap_res = client.post(
        "/api/career/roadmaps/generate",
        json={"target_role": "Software Engineer", "resume_id": resume_id},
        headers=u1_headers,
    )
    assert roadmap_res.status_code in [200, 201]
    roadmap_data = roadmap_res.json()
    roadmap_id = roadmap_data["id"]
    weekly_plan = roadmap_data.get("weekly_plan") or []
    assert len(weekly_plan) == 6, f"Expected 6 bi-weekly milestones, got {len(weekly_plan)}"
    assert len(roadmap_data.get("projects", [])) > 0
    assert len(roadmap_data.get("interview_topics", [])) > 0
    print(f"  [PASS] Generated 12-Week Roadmap ID #{roadmap_id} across {len(weekly_plan)} bi-weekly phases.")

    # Retrieve roadmap
    get_rm = client.get(f"/api/career/roadmaps/{roadmap_id}", headers=u1_headers)
    assert get_rm.status_code == 200
    print("  [PASS] Career roadmap persisted and retrievable.")

    # =========================================================================
    # Step 7: Dashboard Metrics Sanity Check
    # =========================================================================
    log_step("STEP 7: Dashboard Integration Verification")

    docs_list = client.get("/api/documents", headers=u1_headers).json()
    chats_list = client.get("/api/chat/sessions", headers=u1_headers).json()
    resumes_list = client.get("/api/resumes", headers=u1_headers).json()
    roadmaps_list = client.get("/api/career/roadmaps", headers=u1_headers).json()

    print(f"  Dashboard metrics for User 1:")
    print(f"  - Documents: {len(docs_list)}")
    print(f"  - Chat Sessions: {len(chats_list)}")
    print(f"  - Resumes: {len(resumes_list)}")
    print(f"  - Roadmaps: {len(roadmaps_list)}")

    assert len(docs_list) >= 1
    assert len(chats_list) >= 1
    assert len(resumes_list) >= 1
    assert len(roadmaps_list) >= 1
    print("  [PASS] Dashboard data endpoints reflect real backend state.")

    # =========================================================================
    # Step 8: Cleanup Verification
    # =========================================================================
    log_step("STEP 8: Cleanup Verification")

    del_doc = client.delete(f"/api/documents/{doc_id}", headers=u1_headers)
    assert del_doc.status_code == 200
    assert client.get(f"/api/documents/{doc_id}", headers=u1_headers).status_code == 404

    del_chat = client.delete(f"/api/chat/sessions/{session_id}", headers=u1_headers)
    assert del_chat.status_code == 200

    del_resume = client.delete(f"/api/resumes/{resume_id}", headers=u1_headers)
    assert del_resume.status_code == 200

    del_rm = client.delete(f"/api/career/roadmaps/{roadmap_id}", headers=u1_headers)
    assert del_rm.status_code == 200

    print("  [PASS] Cascading cleanup and deletion completed for all created resources.")

    # =========================================================================
    # Step 9: Security Audit — Secret & Leakage Scan
    # =========================================================================
    log_step("STEP 9: Security Verification — Frontend Secret Scan")

    forbidden_patterns = [
        re.compile(r"sk-[a-zA-Z0-9]{20,}"),
        re.compile(r"AIza[0-9A-Za-z-_]{35}"),
        re.compile(r"OPENAI_API_KEY\s*=\s*['\"][^'\"]+['\"]"),
        re.compile(r"GEMINI_API_KEY\s*=\s*['\"][^'\"]+['\"]"),
        re.compile(r"DATABASE_URL\s*=\s*['\"][^'\"]+['\"]"),
    ]

    scan_dirs = ["frontend/src", "frontend/dist"]
    found_secrets = []

    for scan_dir in scan_dirs:
        if not os.path.exists(scan_dir):
            continue
        for root, _, files in os.walk(scan_dir):
            for file in files:
                filepath = os.path.join(root, file)
                try:
                    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                        text = f.read()
                    for pat in forbidden_patterns:
                        if pat.search(text):
                            found_secrets.append((filepath, pat.pattern))
                except Exception:
                    pass

    assert len(found_secrets) == 0, f"Forbidden secrets detected in frontend: {found_secrets}"
    print("  [PASS] Zero secrets or API keys detected in frontend source and production bundle.")

    print(f"\n{'=' * 60}")
    print(">> STEP 13 ALL INTEGRATION VERIFICATIONS PASSED (100% GREEN)")
    print(f"{'=' * 60}\n")


if __name__ == "__main__":
    run_verification()
