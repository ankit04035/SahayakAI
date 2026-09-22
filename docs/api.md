# SahayakAI — REST API Reference (Step 11 Freeze)

**Base URL:** `http://127.0.0.1:8000/api`  
**Interactive Docs:** `http://127.0.0.1:8000/docs` (OpenAPI Swagger UI)  
**ReDoc:** `http://127.0.0.1:8000/redoc`  
**OpenAPI Specification:** `http://127.0.0.1:8000/openapi.json`  
**Frontend Contract:** See [`docs/frontend_contract.md`](frontend_contract.md)

---

## Global Request Headers
- `Content-Type`: `application/json` (or `multipart/form-data` for file uploads)
- `X-User-Id`: Optional integer header for scoping resource access to a specific user (HTTP 403 on cross-user access).

---

## Endpoint Summary (33 Total Endpoints)

### 1. Health & Status
| Method | Path | Status | Description |
|---|---|---|---|
| `GET` | `/api/health` | 200 / 503 | System liveness, database status, AI provider mode, version |

### 2. Document Management & RAG Grounding
| Method | Path | Status | Description |
|---|---|---|---|
| `POST` | `/api/documents/upload` | 201 | Upload & chunk PDF/TXT reference document |
| `GET` | `/api/documents` | 200 | List uploaded reference documents |
| `GET` | `/api/documents/{id}` | 200 | Get document metadata and statistics |
| `DELETE` | `/api/documents/{id}` | 200 | Delete document and cascade chunks / disk file |
| `GET` | `/api/documents/{id}/chunks` | 200 | List paginated text chunks for a document |
| `POST` | `/api/documents/{id}/embed` | 200 | Compute 384-dim embeddings for all chunks |
| `POST` | `/api/documents/{id}/ask` | 200 | Ask question grounded in document (direct RAG) |

### 3. Study Assistant & Conversational Chat
| Method | Path | Status | Description |
|---|---|---|---|
| `POST` | `/api/chat/sessions` | 201 | Create chat session (optionally document-grounded) |
| `GET` | `/api/chat/sessions` | 200 | List chat sessions for requesting user |
| `GET` | `/api/chat/sessions/{id}` | 200 | Get details for specific chat session |
| `DELETE` | `/api/chat/sessions/{id}` | 200 | Delete chat session and cascade messages |
| `POST` | `/api/chat/sessions/{id}/messages` | 200 | Send message and receive grounded AI response |
| `GET` | `/api/chat/sessions/{id}/messages` | 200 | List chronological conversation message history |

### 4. Resume Analyzer & ATS Evaluation
| Method | Path | Status | Description |
|---|---|---|---|
| `POST` | `/api/resumes` | 201 | Upload candidate resume (.pdf or .txt) |
| `GET` | `/api/resumes` | 200 | List candidate resumes |
| `GET` | `/api/resumes/{id}` | 200 | Get resume metadata and storage status |
| `DELETE` | `/api/resumes/{id}` | 200 | Delete resume, linked analyses, and disk file |
| `POST` | `/api/resumes/{id}/analyze` | 200 | Run ATS evaluation against target job description |
| `GET` | `/api/resumes/{id}/analyses` | 200 | List historical ATS evaluations for resume |
| `GET` | `/api/resumes/{id}/analyses/{analysis_id}` | 200 | Get specific ATS evaluation details |

### 5. Career Profile & Personalized Roadmap
| Method | Path | Status | Description |
|---|---|---|---|
| `POST` | `/api/career/profile` | 201 | Create candidate career profile |
| `GET` | `/api/career/profile` | 200 | Get candidate career profile |
| `PUT` | `/api/career/profile` | 200 | Update candidate career profile |
| `DELETE` | `/api/career/profile` | 200 | Delete candidate career profile and roadmaps |
| `POST` | `/api/career/roadmaps/generate` | 201 | Generate 12-week roadmap (with optional resume) |
| `GET` | `/api/career/roadmaps` | 200 | List roadmaps for candidate |
| `GET` | `/api/career/roadmaps/{id}` | 200 | Get specific career roadmap |
| `DELETE` | `/api/career/roadmaps/{id}` | 200 | Delete specific career roadmap |
