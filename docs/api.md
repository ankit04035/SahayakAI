# SahayakAI — REST API Reference

**Base URL:** `http://127.0.0.1:8000/api`  
**Interactive Docs:** `http://127.0.0.1:8000/docs` (OpenAPI Swagger UI)  

---

## 1. System & Health Endpoints

### `GET /api/health`
Returns system status, active environment, and version information.

**Response (200 OK):**
```json
{
  "status": "healthy",
  "app_name": "SahayakAI",
  "environment": "development",
  "version": "0.1.0"
}
```

---

## 2. Document Ingestion Endpoints

### `POST /api/documents/upload`
Uploads a document (PDF or TXT) with automatic text cleaning, chunking, and optional embedding generation.

- **Content-Type:** `multipart/form-data`
- **Parameters:**
  - `file`: File upload (`.txt` or `.pdf`, max 10MB)
  - `auto_embed`: Boolean form field (default: `true`). If true, automatically generates and persists 384-dim embeddings.

**Response (201 Created):**
```json
{
  "id": 1,
  "original_filename": "os_concepts.txt",
  "file_type": "txt",
  "file_size": 2048,
  "processing_status": "completed",
  "chunk_count": 4,
  "created_at": "2026-09-22T14:30:00Z"
}
```

### `GET /api/documents`
Lists all uploaded documents.

### `GET /api/documents/{document_id}`
Returns metadata and status for a specific document.

### `GET /api/documents/{document_id}/chunks`
Lists all text chunks extracted from a specific document.

### `DELETE /api/documents/{document_id}`
Deletes a document and cascades deletion to all associated chunks and embeddings.

---

## 3. RAG & Vector Retrieval Endpoints

### `POST /api/documents/{document_id}/ask`
Performs grounded Question & Answering against the specified document using vector similarity search and LLM synthesis.

- **Request Body (`application/json`):**
```json
{
  "question": "What causes thrashing and how does it affect computer performance?",
  "top_k": 5,
  "similarity_threshold": 0.35
}
```

- **Response (200 OK — Grounded Answer):**
```json
{
  "answer": "Thrashing occurs when a computer virtual memory subsystem is in a constant state of paging...",
  "grounded": true,
  "provider": "demo",
  "model": "demo-deterministic",
  "sources": [
    {
      "chunk_id": 14,
      "chunk_index": 2,
      "page": 1,
      "similarity": 0.6195
    }
  ],
  "query": "What causes thrashing and how does it affect computer performance?",
  "retrieved_count": 1,
  "insufficient_evidence": false
}
```

- **Response (200 OK — Insufficient Evidence):**
```json
{
  "answer": "The provided document does not contain sufficient relevant information to answer this question.",
  "grounded": false,
  "provider": "demo",
  "model": "demo-deterministic",
  "sources": [],
  "query": "What is the recipe for baking chocolate cookies?",
  "retrieved_count": 0,
  "insufficient_evidence": true
}
```

- **Error Responses:**
  - `400 Bad Request`: Document has not been processed or contains no text chunks.
  - `404 Not Found`: Document ID does not exist.
  - `422 Unprocessable Entity`: Document chunks have not been embedded yet, or query validation failed.

### `POST /api/documents/{document_id}/embed`
Triggers or re-runs embedding generation across all chunks of an uploaded document using `all-MiniLM-L6-v2`.

- **Response (200 OK):**
```json
{
  "document_id": 1,
  "embedded_chunks": 4,
  "status": "completed"
}
```
