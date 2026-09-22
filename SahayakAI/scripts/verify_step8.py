"""
Live Smoke Verification Script for Step 8: Study Assistant & Document-Grounded Chat.
Exercises the live FastAPI application and Chat service end-to-end:
1. Health endpoint verification.
2. General study session creation & Q&A turn (no document).
3. Multi-turn conversation history verification.
4. Document upload, embedding & document-grounded session creation.
5. Grounded Q&A turn with vector retrieval citations.
6. Out-of-context query in document session verifying insufficient evidence handling.
7. Message history inspection endpoint.
8. Security & ownership verification (cross-user 403).
9. Session deletion and cleanup.
"""

import io
import os
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, os.path.abspath("."))

from fastapi.testclient import TestClient
from backend.app.config import get_settings
from backend.app.database import SessionLocal
from backend.app.main import app
from backend.app.models.chat import ChatMessage, ChatSession
from backend.app.models.document import Document, DocumentChunk
from backend.app.models.user import User


def run_smoke_verification():
    sep = "=" * 70
    print(sep)
    print("SAHAYAKAI STEP 8 LIVE SMOKE VERIFICATION: STUDY ASSISTANT & CHAT")
    print(sep)

    client = TestClient(app)
    settings = get_settings()
    print("[*] Configuration:")
    print(f"    - Provider Mode: {settings.AI_PROVIDER}")
    print(f"    - Embedding Model: {settings.EMBEDDING_MODEL}")
    print(f"    - Chat Max Message Chars: {settings.CHAT_MAX_MESSAGE_CHARS}")
    print(f"    - Chat Max History Messages: {settings.CHAT_HISTORY_MAX_MESSAGES}")
    print(f"    - Chat Max History Chars: {settings.CHAT_MAX_HISTORY_CHARS}")

    # 1. Health check
    print("\n[Step 1] Verifying /api/health endpoint...")
    health_resp = client.get("/api/health")
    assert health_resp.status_code == 200, f"Health check failed: {health_resp.text}"
    health_data = health_resp.json()
    print(f"    -> Status: {health_data.get('status')}, Environment: {health_data.get('environment')}")

    db = SessionLocal()
    doc_id = None
    gen_session_id = None
    doc_session_id = None

    try:
        # 2. General Study Session
        print("\n[Step 2] Creating general study session (no document attached)...")
        gen_sess_resp = client.post(
            "/api/chat/sessions",
            json={"title": "General Algorithms Study"},
        )
        assert gen_sess_resp.status_code == 201, f"Create general session failed: {gen_sess_resp.text}"
        gen_session_id = gen_sess_resp.json()["id"]
        print(f"    -> Session created: ID={gen_session_id}, Title='{gen_sess_resp.json()['title']}'")

        print("    -> Sending study question: 'Explain merge sort time complexity'...")
        q1_resp = client.post(
            f"/api/chat/sessions/{gen_session_id}/messages",
            json={"message": "Explain the time complexity of merge sort."},
        )
        assert q1_resp.status_code == 200, f"Send message failed: {q1_resp.text}"
        res1 = q1_resp.json()
        print(f"    -> Grounded: {res1['grounded']}")
        print(f"    -> Insufficient Evidence: {res1['insufficient_evidence']}")
        print(f"    -> Provider: {res1['provider']} ({res1['model']})")
        print(f"    -> Answer snippet: {res1['assistant_message']['content'][:140]}...")
        assert res1["grounded"] is False
        assert res1["insufficient_evidence"] is False
        assert len(res1["sources"]) == 0

        # 3. Multi-turn Follow-up
        print("\n[Step 3] Sending follow-up turn in general study session...")
        q2_resp = client.post(
            f"/api/chat/sessions/{gen_session_id}/messages",
            json={"message": "How does it compare to quicksort in the worst case?"},
        )
        assert q2_resp.status_code == 200, f"Send follow-up failed: {q2_resp.text}"
        res2 = q2_resp.json()
        print(f"    -> Follow-up Answer snippet: {res2['assistant_message']['content'][:140]}...")

        # Verify message count in session
        hist_resp = client.get(f"/api/chat/sessions/{gen_session_id}/messages")
        assert hist_resp.status_code == 200
        msgs = hist_resp.json()
        print(f"    -> Total messages in general session: {len(msgs)} (expected 4)")
        assert len(msgs) == 4

        # 4. Document-grounded Chat Session
        print("\n[Step 4] Uploading reference document with auto_embed=True...")
        sample_doc = (
            "Distributed Systems and Consensus Protocols.\n\n"
            "The Raft consensus algorithm is designed to be easy to understand compared to Paxos. "
            "It decomposes consensus into three relatively independent subproblems: Leader Election, "
            "Log Replication, and Safety. Raft relies on a strong leader approach where log entries only "
            "flow from the leader to follower nodes. Nodes exist in one of three states: Follower, Candidate, or Leader.\n\n"
            "Split-brain scenario in distributed systems occurs when network partitions divide a cluster into "
            "isolated sub-groups, each erroneously believing it is the sole active cluster. Quorum-based voting "
            "requires a strict majority of nodes (N/2 + 1) to elect a leader, thereby mathematically preventing "
            "dual leaders during any network partition."
        )

        upload_resp = client.post(
            "/api/documents/upload",
            files={"file": ("distributed_systems.txt", io.BytesIO(sample_doc.encode("utf-8")), "text/plain")},
            data={"auto_embed": "true"},
        )
        assert upload_resp.status_code == 201, f"Upload failed: {upload_resp.text}"
        doc_id = upload_resp.json()["id"]
        print(f"    -> Document uploaded: ID={doc_id}, Title='distributed_systems.txt'")

        print(f"    -> Creating document-grounded session for document {doc_id}...")
        doc_sess_resp = client.post(
            "/api/chat/sessions",
            json={"title": "Raft Protocol Study", "document_id": doc_id},
        )
        assert doc_sess_resp.status_code == 201, f"Create grounded session failed: {doc_sess_resp.text}"
        doc_session_id = doc_sess_resp.json()["id"]
        print(f"    -> Grounded session created: ID={doc_session_id}, Document ID={doc_sess_resp.json()['document_id']}")

        # 5. Grounded Q&A Query
        print("\n[Step 5] Asking grounded question: 'How does Raft prevent split-brain?'...")
        grounded_resp = client.post(
            f"/api/chat/sessions/{doc_session_id}/messages",
            json={"message": "How does Raft prevent split-brain scenarios during network partitions?", "top_k": 3},
        )
        assert grounded_resp.status_code == 200, f"Grounded message failed: {grounded_resp.text}"
        res_g = grounded_resp.json()
        print(f"    -> Grounded: {res_g['grounded']}")
        print(f"    -> Insufficient Evidence: {res_g['insufficient_evidence']}")
        print(f"    -> Sources count: {len(res_g['sources'])}")
        assert res_g["grounded"] is True
        assert res_g["insufficient_evidence"] is False
        assert len(res_g["sources"]) > 0
        top_src = res_g["sources"][0]
        print(f"    -> Top source similarity: {top_src['similarity']:.4f} (chunk {top_src['chunk_index']})")
        print(f"    -> Grounded answer snippet: {res_g['assistant_message']['content'][:140]}...")

        # 6. Out-of-context Query (Threshold Gating)
        print("\n[Step 6] Asking irrelevant question in document session...")
        irrel_resp = client.post(
            f"/api/chat/sessions/{doc_session_id}/messages",
            json={"message": "What ingredients are needed to bake sourdough bread at home?", "top_k": 3},
        )
        assert irrel_resp.status_code == 200, f"Irrelevant query failed: {irrel_resp.text}"
        res_i = irrel_resp.json()
        print(f"    -> Grounded: {res_i['grounded']}")
        print(f"    -> Insufficient Evidence: {res_i['insufficient_evidence']}")
        print(f"    -> Assistant response: '{res_i['assistant_message']['content']}'")
        assert res_i["grounded"] is False
        assert res_i["insufficient_evidence"] is True
        assert len(res_i["sources"]) == 0

        # 7. Security / Cross-user test
        print("\n[Step 7] Verifying cross-user access rejection (HTTP 403)...")
        other_user_resp = client.get(f"/api/chat/sessions/{doc_session_id}?user_id=99999")
        print(f"    -> Response status: {other_user_resp.status_code} (expected 403)")
        assert other_user_resp.status_code == 403

        # 8. Session Deletion
        print("\n[Step 8] Deleting general session and verifying cascade...")
        del_resp = client.delete(f"/api/chat/sessions/{gen_session_id}")
        assert del_resp.status_code == 200
        get_del_resp = client.get(f"/api/chat/sessions/{gen_session_id}")
        assert get_del_resp.status_code == 404
        print("    -> Session deleted successfully, 404 confirmed on retrieval.")

    finally:
        # Cleanup DB
        if gen_session_id:
            db.query(ChatMessage).filter(ChatMessage.session_id == gen_session_id).delete()
            db.query(ChatSession).filter(ChatSession.id == gen_session_id).delete()
        if doc_session_id:
            db.query(ChatMessage).filter(ChatMessage.session_id == doc_session_id).delete()
            db.query(ChatSession).filter(ChatSession.id == doc_session_id).delete()
        if doc_id:
            db.query(DocumentChunk).filter(DocumentChunk.document_id == doc_id).delete()
            db.query(Document).filter(Document.id == doc_id).delete()
        db.commit()
        db.close()

    print("\n" + sep)
    print("ALL STEP 8 LIVE SMOKE VERIFICATION CHECKS PASSED SUCCESSFULLY!")
    print(sep)


if __name__ == "__main__":
    run_smoke_verification()
