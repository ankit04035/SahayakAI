# SahayakAI — AI-Powered Career & Academic Mentor

[![Tests: 236 Passed](https://img.shields.io/badge/Tests-236%20Passed-brightgreen.svg)]()
[![Python: 3.12](https://img.shields.io/badge/Python-3.12-blue.svg)]()
[![FastAPI: 0.115](https://img.shields.io/badge/FastAPI-0.115-teal.svg)]()
[![Model: all--MiniLM--L6--v2](https://img.shields.io/badge/Embeddings-all--MiniLM--L6--v2-orange.svg)]()
[![License: MIT](https://img.shields.io/badge/License-MIT-purple.svg)]()

> **SahayakAI** is an intelligent, offline-capable, and privacy-first career advancement and study copilot. Built for students and early-career developers, SahayakAI integrates reference document processing, semantic vector search (RAG), conversational study assistance, transparent ATS resume scoring, and milestone-based career roadmap generation into a hardened, production-ready backend.

---

## Current Status: STEP 11 Complete ✅

- **Step 2:** FastAPI Foundation & Structured Errors ✅
- **Step 3:** SQLAlchemy Models & Database Schemas ✅
- **Step 4:** AI Provider Abstraction (`DemoProvider`, `OpenAICompatibleProvider`, `GeminiProvider`) ✅
- **Step 5:** Document Processing & Boundary-Aware NLP Chunking ✅
- **Step 6:** Transformer Sentence Embeddings (`all-MiniLM-L6-v2`, 384-dim) ✅
- **Step 7:** Vector Retrieval & Grounded RAG Pipeline ✅
- **Step 8:** Conversational Study Assistant & Multi-Turn Chat ✅
- **Step 9:** Resume Analyzer & ATS Evaluation Scorecard ✅
- **Step 10:** Career Profile & Personalized Career Roadmap ✅
- **Step 11:** Backend Integration, API Contract Hardening & Pre-Frontend Verification ✅
  - **236 / 236 Automated Tests Passing (100% Green)**
  - **End-to-End Synthetic User Journey Script (`scripts/verify_step11.py`) Passing Steps A–P**
  - **Frontend Contract Documented (`docs/frontend_contract.md`)**
  - **100% Dual-Directory Parity (`/` and `SahayakAI/`)**

---

## Key Features

1. **Deterministic Demo Mode**: Complete offline operation with zero API keys or billing overhead.
2. **Document Study & Grounded Chat**: Upload PDF/TXT study guides and ask document-grounded questions with traceable citation sources.
3. **Transparent ATS Resume Analyzer**: Skill extraction, alias normalization, and transparent scorecard matching against target job descriptions.
4. **Milestone Career Roadmaps**: 12-week pedagogical skill roadmaps, project recommendations, and technical interview questions based on curated role taxonomies.
5. **Strict User-Scoping Security**: Per-user resource isolation across all endpoints via `X-User-Id` header (HTTP 403 on cross-user access).
6. **Hardened API Contracts**: Uniform error envelopes, OpenAPI 3.x schema, Swagger UI (`/docs`), and ReDoc (`/redoc`).

---

## Quick Start

### 1. Prerequisites & Installation
```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Run Test Suite
```powershell
python -m pytest -v
```
*(All 236 tests pass in ~45 seconds on standard CPU)*

### 3. Run Live End-to-End Synthetic Verification
```powershell
python scripts/verify_step11.py
```

### 4. Start Development Server
```powershell
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```
- Interactive API Docs: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
- Health Check: `http://localhost:8000/api/health`

---

## API Summary

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/health` | System liveness, database status, AI provider mode |
| `POST` | `/api/documents/upload` | Upload & chunk PDF/TXT study documents |
| `GET` | `/api/documents` | List uploaded reference documents |
| `GET` | `/api/documents/{id}` | Get document metadata, extracted text & stats |
| `DELETE` | `/api/documents/{id}` | Delete document and cascade chunks / disk files |
| `POST` | `/api/documents/{id}/embed` | Compute and store 384-dim chunk embeddings |
| `POST` | `/api/documents/{id}/ask` | Direct RAG semantic query against document |
| `POST` | `/api/chat/sessions` | Create conversational study chat session |
| `GET` | `/api/chat/sessions` | List user chat sessions |
| `POST` | `/api/chat/sessions/{id}/messages` | Send grounded chat message (RAG synthesis) |
| `GET` | `/api/chat/sessions/{id}/messages` | List conversation message history |
| `POST` | `/api/resumes` | Upload candidate resume (.pdf or .txt) |
| `GET` | `/api/resumes` | List candidate resumes |
| `POST` | `/api/resumes/{id}/analyze` | Compute ATS match score & missing skills against JD |
| `POST` | `/api/career/profile` | Upsert candidate career profile |
| `GET` | `/api/career/profile` | Get candidate career profile |
| `POST` | `/api/career/roadmaps/generate` | Generate 12-week roadmap (with optional resume) |
| `GET` | `/api/career/roadmaps` | List user career roadmaps |
| `GET` | `/api/career/roadmaps/{id}` | Get specific career roadmap |

---

## Documentation
- [Frontend Integration Contract](docs/frontend_contract.md)
- [System Architecture](docs/architecture.md)
- [Architecture Decision Records (ADRs)](docs/decisions.md)
- [API Reference](docs/api.md)
- [Career Roadmap Specification](docs/career_roadmap.md)
