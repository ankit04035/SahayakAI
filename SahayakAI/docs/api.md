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

---

## 4. Chat & Study Assistant Endpoints

### `POST /api/chat/sessions`
Creates a new conversational chat session.

- **Request Body (`application/json`):**
```json
{
  "title": "Operating Systems Revision",
  "document_id": 1,
  "user_id": null
}
```
- **Response (201 Created):**
```json
{
  "id": 1,
  "user_id": 1,
  "title": "Operating Systems Revision",
  "document_id": 1,
  "created_at": "2026-09-22T16:00:00Z",
  "updated_at": "2026-09-22T16:00:00Z"
}
```

### `GET /api/chat/sessions`
Lists chat sessions belonging to the user.
- **Query Parameters:** `document_id` (optional), `user_id` (optional)
- **Headers:** `X-User-Id` (optional)

### `GET /api/chat/sessions/{session_id}`
Retrieves session metadata. Enforces user ownership (403 if unauthorized).

### `DELETE /api/chat/sessions/{session_id}`
Deletes a chat session and cascades deletion to all messages.

### `POST /api/chat/sessions/{session_id}/messages`
Submits a user question to the study assistant.
- **Request Body (`application/json`):**
```json
{
  "message": "What is thrashing and how does the OS mitigate it?",
  "top_k": 3,
  "similarity_threshold": 0.35
}
```
- **Response (200 OK — Grounded Document Answer):**
```json
{
  "session_id": 1,
  "user_message": {
    "id": 10,
    "session_id": 1,
    "role": "user",
    "content": "What is thrashing and how does the OS mitigate it?",
    "created_at": "2026-09-22T16:05:00Z"
  },
  "assistant_message": {
    "id": 11,
    "session_id": 1,
    "role": "assistant",
    "content": "Thrashing occurs when a computer's virtual memory subsystem...",
    "source_metadata": {
      "grounded": true,
      "insufficient_evidence": false,
      "sources": [{"chunk_id": 4, "chunk_index": 2, "page": 1, "similarity": 0.6195}]
    },
    "created_at": "2026-09-22T16:05:01Z"
  },
  "grounded": true,
  "insufficient_evidence": false,
  "sources": [
    {
      "chunk_id": 4,
      "chunk_index": 2,
      "page": 1,
      "similarity": 0.6195
    }
  ],
  "provider": "demo",
  "model": "demo-deterministic"
}
```

### `GET /api/chat/sessions/{session_id}/messages`
Retrieves chronological message history for a session.

---

## 5. Resume Analyzer & ATS Scorecard Endpoints

### `POST /api/resumes`
Uploads a candidate resume (`.pdf` or `.txt`) with size validation (up to 10MB), path traversal sanitization, and secure disk persistence.
- **Content-Type:** `multipart/form-data`
- **Form Fields:** `file` (required), `user_id` (optional)
- **Headers:** `X-User-Id` (optional)
- **Response (201 Created):**
```json
{
  "id": 1,
  "user_id": 1,
  "original_filename": "ananya_resume.txt",
  "stored_filename": "a1b2c3d4_ananya_resume.txt",
  "file_type": ".txt",
  "file_size": 2048,
  "processing_status": "completed",
  "created_at": "2026-09-22T16:20:00Z",
  "updated_at": "2026-09-22T16:20:00Z"
}
```

### `GET /api/resumes`
Lists all resumes belonging to the requesting user.
- **Headers:** `X-User-Id` (optional)
- **Response (200 OK):** Array of resume records.

### `GET /api/resumes/{resume_id}`
Retrieves metadata for a specific resume. Enforces user ownership (403 if unauthorized).

### `DELETE /api/resumes/{resume_id}`
Deletes a resume, removes the stored file from disk, and cascades deletion to all associated analysis records.

### `POST /api/resumes/{resume_id}/analyze`
Extracts structured skills, education, and experience, and evaluates against an optional job description.
- **Request Body (`application/json`, optional):**
```json
{
  "job_description": "Seeking a Backend Engineer proficient in Python, FastAPI, Docker, Kubernetes, and AWS."
}
```
- **Response (200 OK — With Job Description):**
```json
{
  "id": 1,
  "resume_id": 1,
  "job_description": "Seeking a Backend Engineer proficient in Python, FastAPI, Docker, Kubernetes, and AWS.",
  "extracted_skills": ["Docker", "FastAPI", "Git", "PostgreSQL", "Python", "React", "Redis"],
  "education_data": [
    {
      "degree": "BACHELOR OF TECHNOLOGY",
      "institution": "Delhi Technological University",
      "year": "2022",
      "description": "Bachelor of Technology in Computer Science, Delhi Technological University, 2022"
    }
  ],
  "experience_data": [
    {
      "role": "Software Engineer",
      "company": "CloudSystems Inc",
      "duration": "Jan 2022 to Present",
      "description": "Software Engineer - CloudSystems Inc - Jan 2022 to Present"
    }
  ],
  "matched_skills": ["Docker", "FastAPI", "Python"],
  "missing_skills": ["AWS", "Kubernetes"],
  "match_score": 60.0,
  "recommendations": [
    "Target Skill Development: Consider acquiring or highlighting hands-on project experience in: AWS, Kubernetes.",
    "Quantifiable Achievements: Strengthen bullet points by quantifying accomplishments with measurable metrics (e.g., % latency reduction, user scale, efficiency gains)."
  ],
  "created_at": "2026-09-22T16:25:00Z",
  "updated_at": "2026-09-22T16:25:00Z"
}
```

### `GET /api/resumes/{resume_id}/analyses`
Retrieves historical analysis records for a resume.

### `GET /api/resumes/{resume_id}/analyses/{analysis_id}`
Retrieves a specific analysis scorecard by ID. Enforces ownership check.
