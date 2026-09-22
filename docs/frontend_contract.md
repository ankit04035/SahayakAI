# SahayakAI — Frontend Integration Contract (Step 11 Freeze)

**Target Milestone:** STEP 12 (Frontend Development)  
**Status:** FROZEN & VERIFIED  
**Baseline Backend Test Coverage:** 236 / 236 Passing  
**API Documentation:** Interactive Swagger UI at `http://localhost:8000/docs`, ReDoc at `http://localhost:8000/redoc`, OpenAPI JSON at `http://localhost:8000/openapi.json`.

---

## 1. Global API Standards

### Base URL
```
http://localhost:8000/api
```

### Required Request Headers
| Header | Description | Default / Example |
|---|---|---|
| `Content-Type` | `application/json` (or `multipart/form-data` for file uploads) | `application/json` |
| `X-User-Id` | Optional in pre-auth dev; when supplied, strictly scopes all resource access, queries, and mutations to the specified user ID. | `1` |

### CORS Configuration
- **Allowed Origins:** `http://localhost:5173` (configured Vite default)
- **Allowed Methods:** `GET`, `POST`, `PUT`, `DELETE`, `OPTIONS`, `PATCH`
- **Allowed Headers:** `*`
- **Credentials:** `true`

---

## 2. Standardized Error Response Envelope

All application exceptions, validation failures, and unhandled errors return a consistent JSON envelope:

```json
{
  "status": "error",
  "error_code": "ERROR_CODE_STRING",
  "message": "Human-readable explanation of the issue.",
  "details": null
}
```

### Standard Error Codes
| HTTP Status | Error Code | Description |
|---|---|---|
| `400` | `INVALID_MESSAGE` / `DOCUMENT_PROCESSING_FAILED` / `ROADMAP_GENERATION_ERROR` | Business logic or request validation failed. |
| `403` | `DOCUMENT_ACCESS_DENIED` / `SESSION_ACCESS_DENIED` / `RESUME_ACCESS_DENIED` / `PROFILE_ACCESS_DENIED` / `ROADMAP_ACCESS_DENIED` | Requesting user does not own the requested resource. |
| `404` | `DOCUMENT_NOT_FOUND` / `SESSION_NOT_FOUND` / `RESUME_NOT_FOUND` / `PROFILE_NOT_FOUND` / `ROADMAP_NOT_FOUND` | Target resource does not exist. |
| `422` | `VALIDATION_ERROR` | Pydantic schema validation error (details contains list of error fields). |
| `500` | `INTERNAL_SERVER_ERROR` | Unexpected server exception (safe message, no stack traces or secrets exposed). |
| `503` | `DATABASE_ERROR` | Database connectivity failure or degraded service status. |

---

## 3. API Endpoint Contracts

### 3.1 Health & Liveness
#### `GET /api/health`
- **Response (200 OK):**
```json
{
  "status": "ok",
  "database": "ok",
  "ai_provider": "demo",
  "version": "0.1.0"
}
```
- **Degraded (503 Service Unavailable):**
```json
{
  "status": "degraded",
  "database": "error",
  "ai_provider": "demo",
  "version": "0.1.0"
}
```

---

### 3.2 Reference Documents & RAG Grounding
#### `POST /api/documents/upload`
- **Content-Type:** `multipart/form-data`
- **Form Fields:**
  - `file`: PDF or TXT binary file (Max 10MB)
  - `title`: string (optional)
  - `auto_embed`: boolean (default `true`)
  - `user_id`: integer (optional, overridden by `X-User-Id`)
- **Response (201 Created):**
```json
{
  "id": 1,
  "user_id": 1,
  "title": "Systems Architecture Guide",
  "original_filename": "systems_architecture.txt",
  "stored_filename": "systems_architecture_a1b2c3d4.txt",
  "file_type": "txt",
  "file_size": 2048,
  "mime_type": "text/plain",
  "processing_status": "completed",
  "character_count": 1850,
  "word_count": 280,
  "page_count": 1,
  "chunk_count": 4,
  "primary_language": "en",
  "keywords": ["microservices", "architecture", "fastapi"],
  "created_at": "2026-09-22T23:00:00Z"
}
```

#### `GET /api/documents`
- **Query Params:** `skip` (int, default 0), `limit` (int, default 50)
- **Response (200 OK):** List of `DocumentRead` objects.

#### `GET /api/documents/{document_id}`
- **Response (200 OK):** `DocumentDetailRead` (includes `extracted_text`, `keywords`, `chunk_count`).

#### `GET /api/documents/{document_id}/chunks`
- **Query Params:** `skip` (int, default 0), `limit` (int, default 50)
- **Response (200 OK):** List of `DocumentChunkRead` objects (`chunk_index`, `content`, `character_count`, `chunk_metadata`).

#### `DELETE /api/documents/{document_id}`
- **Response (200 OK):** `{"message": "Document deleted successfully", "id": 1}`

#### `POST /api/documents/{document_id}/embed`
- **Response (200 OK):** `{"document_id": 1, "embedded_chunks": 4, "status": "completed"}`

#### `POST /api/documents/{document_id}/ask`
- **Request Body:**
```json
{
  "question": "How do microservices interact?",
  "top_k": 5,
  "similarity_threshold": 0.35
}
```
- **Response (200 OK):** `RAGQueryResponse` (`answer`, `grounded`, `provider`, `model`, `sources`, `insufficient_evidence`).

---

### 3.3 Study Assistant & Grounded Chat
#### `POST /api/chat/sessions`
- **Request Body:**
```json
{
  "title": "Microservices Discussion",
  "document_id": 1
}
```
- **Response (201 Created):** `ChatSessionRead` (`id`, `user_id`, `title`, `document_id`, `created_at`, `updated_at`).

#### `GET /api/chat/sessions`
- **Response (200 OK):** List of `ChatSessionRead` objects for the requesting user.

#### `GET /api/chat/sessions/{session_id}`
- **Response (200 OK):** `ChatSessionRead`

#### `DELETE /api/chat/sessions/{session_id}`
- **Response (200 OK):** `{"message": "Chat session deleted successfully", "id": 1}`

#### `POST /api/chat/sessions/{session_id}/messages`
- **Request Body:**
```json
{
  "message": "Explain how service discovery works.",
  "top_k": 5,
  "similarity_threshold": 0.35
}
```
- **Response (200 OK):**
```json
{
  "session_id": 1,
  "user_message": {
    "id": 10,
    "session_id": 1,
    "role": "user",
    "content": "Explain how service discovery works.",
    "source_metadata": null,
    "created_at": "2026-09-22T23:05:00Z"
  },
  "assistant_message": {
    "id": 11,
    "session_id": 1,
    "role": "assistant",
    "content": "Service discovery allows services to dynamically discover endpoint addresses...",
    "source_metadata": [{"chunk_id": 2, "chunk_index": 1, "page": 1, "similarity": 0.88}],
    "created_at": "2026-09-22T23:05:01Z"
  },
  "grounded": true,
  "insufficient_evidence": false,
  "sources": [{"chunk_id": 2, "chunk_index": 1, "page": 1, "similarity": 0.88}],
  "provider": "demo",
  "model": "demo-v1"
}
```

#### `GET /api/chat/sessions/{session_id}/messages`
- **Response (200 OK):** Chronological list of `ChatMessageRead` objects.

---

### 3.4 Resume Analyzer & ATS Scorecard
#### `POST /api/resumes`
- **Content-Type:** `multipart/form-data`
- **Form Fields:** `file` (.pdf or .txt)
- **Response (201 Created):** `ResumeRead` (`id`, `user_id`, `original_filename`, `file_type`, `file_size`, `processing_status`, `created_at`).

#### `GET /api/resumes`
- **Response (200 OK):** List of `ResumeRead` objects.

#### `GET /api/resumes/{resume_id}`
- **Response (200 OK):** `ResumeRead`

#### `DELETE /api/resumes/{resume_id}`
- **Response (200 OK):** `{"message": "Resume deleted successfully", "id": 1}`

#### `POST /api/resumes/{resume_id}/analyze`
- **Request Body:**
```json
{
  "job_description": "Seeking a Backend Engineer with Python, FastAPI, Docker, and Kubernetes experience."
}
```
- **Response (200 OK):**
```json
{
  "id": 1,
  "resume_id": 1,
  "job_description": "Seeking a Backend Engineer...",
  "match_score": 75.0,
  "extracted_skills": ["Python", "FastAPI", "Docker", "SQL"],
  "matched_skills": ["Docker", "FastAPI", "Python"],
  "missing_skills": ["Kubernetes"],
  "recommendations": [
    "Consider highlighting practical Kubernetes experience.",
    "Add metrics showing impact of deployed microservices."
  ],
  "education_data": [{"degree": "B.Tech Computer Science", "year": "2023"}],
  "experience_data": [{"role": "Backend Engineer", "company": "CloudCorp"}],
  "created_at": "2026-09-22T23:10:00Z"
}
```

#### `GET /api/resumes/{resume_id}/analyses`
- **Response (200 OK):** List of `ResumeAnalysisRead` objects.

#### `GET /api/resumes/{resume_id}/analyses/{analysis_id}`
- **Response (200 OK):** `ResumeAnalysisRead`

---

### 3.5 Career Profile & Personalized Career Roadmap
#### `POST /api/career/profile` (or `PUT /api/career/profile`)
- **Request Body:**
```json
{
  "degree": "B.Tech Computer Science",
  "target_role": "Backend Developer",
  "current_skills": ["Python", "Git", "SQL"],
  "experience": "1 year backend engineering",
  "interests": ["Distributed Systems", "Cloud Computing"]
}
```
- **Response (200 or 201):** `CareerProfileRead` (`id`, `user_id`, `degree`, `target_role`, `current_skills`, `experience`, `interests`, `created_at`, `updated_at`).

#### `GET /api/career/profile`
- **Response (200 OK):** `CareerProfileRead` (or 404 if profile has not been created).

#### `DELETE /api/career/profile`
- **Response (200 OK):** `{"message": "Career profile deleted successfully"}`

#### `POST /api/career/roadmaps/generate`
- **Request Body:**
```json
{
  "target_role": "Backend Developer",
  "resume_id": 1,
  "custom_interests": ["Microservices"]
}
```
- **Response (201 Created):**
```json
{
  "id": 1,
  "career_profile_id": 1,
  "title": "Backend Developer Mastery Roadmap",
  "recommended_skills": ["Docker", "Redis", "FastAPI", "Kubernetes"],
  "missing_skills": ["Kubernetes", "Redis"],
  "projects": [
    {
      "title": "High-Throughput Microservice",
      "skills": ["Python", "FastAPI", "Redis"],
      "difficulty": "Intermediate",
      "description": "Build an asynchronous rate-limited API gateway."
    }
  ],
  "learning_order": ["FastAPI", "Docker", "Redis", "Kubernetes"],
  "weekly_plan": [
    {
      "week_range": "Weeks 1-3",
      "focus": "Foundations & Asynchronous APIs",
      "learning_goals": ["FastAPI dependency injection", "Pydantic data modeling"],
      "deliverable": "CRUD REST API"
    }
  ],
  "interview_topics": ["Database indexing", "Concurrency in Python", "CAP Theorem"],
  "recommendation_reasons": ["Kubernetes is highly demanded for Backend Developer roles."],
  "created_at": "2026-09-22T23:15:00Z",
  "updated_at": "2026-09-22T23:15:00Z"
}
```

#### `GET /api/career/roadmaps`
- **Response (200 OK):** List of `RoadmapRead` objects.

#### `GET /api/career/roadmaps/{roadmap_id}`
- **Response (200 OK):** `RoadmapRead` (or 403 / 404).

#### `DELETE /api/career/roadmaps/{roadmap_id}`
- **Response (200 OK):** `{"message": "Roadmap deleted successfully", "id": 1}`
