"""
Live Smoke Verification Script for Step 7: Vector Retrieval & RAG Pipeline.
Exercises the live FastAPI application and RAG pipeline end-to-end:
1. Health endpoint verification.
2. Document upload and automatic chunking + embedding.
3. RAG Q&A query with grounded English context -> validates grounded answer and citations.
4. RAG Q&A query with concept query -> validates retrieval and answer.
5. RAG Q&A query with completely unrelated out-of-context question -> validates threshold gating and insufficient_evidence response.
6. Direct retrieval and similarity checks.
7. Explicit POST /api/documents/{id}/embed re-embedding endpoint verification.
8. Proper cleanup.
"""

import io
import os
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, os.path.abspath("."))

from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.database import SessionLocal
from backend.app.models.document import Document, DocumentChunk
from backend.app.config import get_settings

def run_smoke_verification():
    sep = "=" * 70
    print(sep)
    print("SAHAYAKAI STEP 7 LIVE SMOKE VERIFICATION: VECTOR RETRIEVAL & RAG")
    print(sep)

    client = TestClient(app)
    settings = get_settings()
    print(f"[*] Configuration:")
    print(f"    - Provider Mode: {settings.AI_PROVIDER}")
    print(f"    - Embedding Model: {settings.EMBEDDING_MODEL}")
    print(f"    - Embedding Dim: {settings.EMBEDDING_DIMENSION}")
    print(f"    - RAG Top-K: {settings.RAG_TOP_K}")
    print(f"    - RAG Similarity Threshold: {settings.RAG_SIMILARITY_THRESHOLD}")
    print(f"    - RAG Max Context Chars: {settings.RAG_MAX_CONTEXT_CHARS}")

    print("\n[Step 1] Verifying /api/health endpoint...")
    health_resp = client.get("/api/health")
    assert health_resp.status_code == 200, f"Health check failed: {health_resp.text}"
    health_data = health_resp.json()
    print(f"    -> Status: {health_data.get('status')}, Environment: {health_data.get('environment')}")

    print("\n[Step 2] Uploading technical document with auto_embed=True...")
    sample_content = (
        "Operating Systems and Memory Management.\n\n"
        "Virtual memory is a memory management capability of an operating system that uses hardware "
        "and software to allow a computer to compensate for physical memory shortages by temporarily "
        "transferring data from random access memory (RAM) to disk storage. Paging is a memory management "
        "scheme by which a computer stores and retrieves data from secondary storage for use in main memory.\n\n"
        "A page fault occurs when a program attempts to access a block of memory that is not stored in the "
        "physical RAM. In response, the operating system kernel loads the missing page from disk into RAM. "
        "Page replacement algorithms such as Least Recently Used (LRU) and First-In First-Out (FIFO) "
        "determine which memory page to evict when physical frames are exhausted.\n\n"
        "Thrashing occurs when a computer virtual memory subsystem is in a constant state of paging, "
        "rapidly exchanging data in memory for data on disk, to the exclusion of most real application processing. "
        "This causes the computer performance to degrade or collapse.\n\n"
        "Deadlock is a state in which each member of a group is waiting for another member, including itself, "
        "to take action, such as sending a message or more commonly releasing a lock. Four conditions must hold "
        "simultaneously for a deadlock to occur: Mutual Exclusion, Hold and Wait, No Preemption, and Circular Wait."
    )

    upload_resp = client.post(
        "/api/documents/upload",
        files={"file": ("os_concepts.txt", io.BytesIO(sample_content.encode("utf-8")), "text/plain")},
        data={"auto_embed": "true"},
    )
    assert upload_resp.status_code == 201, f"Upload failed: {upload_resp.text}"
    doc_data = upload_resp.json()
    doc_id = doc_data["id"]
    print(f"    -> Document uploaded: ID={doc_id}, Title='{doc_data.get('original_filename', doc_data.get('title'))}', Chunks={doc_data['chunk_count']}")

    db = SessionLocal()
    try:
        chunks = db.query(DocumentChunk).filter(DocumentChunk.document_id == doc_id).all()
        assert len(chunks) > 0, "No chunks created"
        embedded_count = sum(1 for c in chunks if c.embedding is not None)
        print(f"    -> Chunks in DB: {len(chunks)}, Embedded: {embedded_count}/{len(chunks)}")
        assert embedded_count == len(chunks), f"Not all chunks were embedded: {embedded_count}/{len(chunks)}"

        print("\n[Step 3] Asking grounded question: 'What causes thrashing and how does it affect performance?'...")
        ask_resp1 = client.post(
            f"/api/documents/{doc_id}/ask",
            json={"question": "What causes thrashing and how does it affect performance?", "top_k": 3},
        )
        assert ask_resp1.status_code == 200, f"Ask failed: {ask_resp1.text}"
        res1 = ask_resp1.json()
        print(f"    -> Grounded: {res1['grounded']}")
        print(f"    -> Insufficient Evidence: {res1['insufficient_evidence']}")
        print(f"    -> Retrieved Chunks: {res1['retrieved_count']}")
        print(f"    -> Answer snippet: {res1['answer'][:160]}...")
        assert res1["grounded"] is True
        assert res1["insufficient_evidence"] is False
        assert len(res1["sources"]) > 0
        top_src = res1["sources"][0]
        print(f"    -> Top source similarity: {top_src['similarity']:.4f} (chunk {top_src['chunk_index']})")
        assert top_src["similarity"] >= settings.RAG_SIMILARITY_THRESHOLD

        print("\n[Step 4] Asking concept query: 'What are the four conditions for deadlock?'...")
        ask_resp2 = client.post(
            f"/api/documents/{doc_id}/ask",
            json={"question": "What are the four conditions for deadlock?", "top_k": 3},
        )
        assert ask_resp2.status_code == 200, f"Deadlock query failed: {ask_resp2.text}"
        res2 = ask_resp2.json()
        print(f"    -> Grounded: {res2['grounded']}")
        print(f"    -> Top source chunk: {res2['sources'][0]['chunk_index']}, Score: {res2['sources'][0]['similarity']:.4f}")
        assert "deadlock" in res2["answer"].lower() or "mutual exclusion" in res2["answer"].lower()

        print("\n[Step 5] Asking completely irrelevant question: 'What is the recipe for baking chocolate cookies?'...")
        ask_resp3 = client.post(
            f"/api/documents/{doc_id}/ask",
            json={"question": "What is the recipe for baking chocolate cookies with brown sugar?", "top_k": 3},
        )
        assert ask_resp3.status_code == 200, f"Out-of-context query failed: {ask_resp3.text}"
        res3 = ask_resp3.json()
        print(f"    -> Grounded: {res3['grounded']}")
        print(f"    -> Insufficient Evidence: {res3['insufficient_evidence']}")
        print(f"    -> Answer: '{res3['answer']}'")
        assert res3["insufficient_evidence"] is True
        assert res3["grounded"] is False
        assert len(res3["sources"]) == 0

        print("\n[Step 6] Testing POST /api/documents/{id}/embed explicit embedding endpoint...")
        embed_resp = client.post(f"/api/documents/{doc_id}/embed")
        assert embed_resp.status_code == 200, f"Embed endpoint failed: {embed_resp.text}"
        embed_data = embed_resp.json()
        print(f"    -> Re-embedded chunks: {embed_data['embedded_chunks']}, Status: {embed_data['status']}")
        assert embed_data["embedded_chunks"] == len(chunks)

        print("\n[Step 7] Cleaning up test document...")
        del_resp = client.delete(f"/api/documents/{doc_id}")
        assert del_resp.status_code == 200, f"Delete failed: {del_resp.text}"
        print("    -> Document deleted successfully.")

    finally:
        db.query(DocumentChunk).filter(DocumentChunk.document_id == doc_id).delete()
        db.query(Document).filter(Document.id == doc_id).delete()
        db.commit()
        db.close()

    print("\n" + sep)
    print("ALL LIVE SMOKE VERIFICATION CHECKS PASSED SUCCESSFULLY!")
    print(sep)

if __name__ == "__main__":
    run_smoke_verification()
