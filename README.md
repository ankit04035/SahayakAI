# SahayakAI — AI-Powered Career & Academic Mentor

[![Tests: 236 Backend Passed](https://img.shields.io/badge/Backend%20Tests-236%20Passed-brightgreen.svg)]()
[![Tests: 19 Frontend Passed](https://img.shields.io/badge/Frontend%20Tests-19%20Passed-brightgreen.svg)]()
[![Security: 23/23 Gates Passed](https://img.shields.io/badge/Security-23%2F23%20Gates%20Passed-brightgreen.svg)]()
[![Python: 3.12](https://img.shields.io/badge/Python-3.12-blue.svg)]()
[![FastAPI: 0.115](https://img.shields.io/badge/FastAPI-0.115-teal.svg)]()
[![React: 18.3](https://img.shields.io/badge/React-18.3-61dafb.svg)]()
[![Vite: 6.0](https://img.shields.io/badge/Vite-6.0-646cff.svg)]()
[![License: MIT](https://img.shields.io/badge/License-MIT-purple.svg)]()

> **SahayakAI (सहायक AI)** is an intelligent, offline-capable, privacy-first career advancement and study copilot. Built for students and early-career developers, SahayakAI integrates reference document processing, semantic vector search (RAG), conversational study assistance, transparent ATS resume scoring, milestone-based career roadmap generation, and a modern React + Vite frontend application.

---

## Current Status: STEP 14 Complete (Production Ready) ✅

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
- **Step 12:** Modern React + Vite Frontend Application ✅
- **Step 13:** Frontend ↔ Backend Integration & End-to-End User Flow Verification ✅
- **Step 14:** Security Hardening, Full End-to-End Verification & Production Readiness ✅
  - **Comprehensive 23-Point Security & E2E Verification**: `scripts/verify_step14.py` (100% green)
  - **Multi-Tenant User Isolation**: Strict ownership checks across all endpoints via `X-User-Id` (HTTP 403 Forbidden)
  - **Safe File Uploads**: Whitelist validation (`.pdf`, `.txt`), 10MB bounds, UUID sanitization, path traversal neutralization
  - **Prompt Injection Resistance**: Cosine similarity gating (0.35) and demarcated prompts preventing system override or credential leaks
  - **Secret Audit**: Zero hardcoded provider API keys across repository, tests, and frontend bundles
  - **Database Integrity**: Cascade deletions without orphan records; `PRAGMA integrity_check;` returns `ok`
  - **Backend Regression Suite**: 236 / 236 pytest tests passing (100% green)
  - **Frontend Test Suite**: 19 / 19 Vitest tests passing (100% green)
  - **Production Build**: Zero-error Vite production build (`npm run build`)
  - **Dual-Directory Parity**: 100% SHA-256 match between root and `SahayakAI/`

---

## Key Features

1. **Deterministic Demo Mode**: Complete offline operation with zero API keys or billing overhead.
2. **Document Study & Grounded Chat**: Upload PDF/TXT study guides, view vector chunk partitions, and ask document-grounded questions with traceable citation sources.
3. **Transparent ATS Resume Analyzer**: Skill extraction, alias normalization, and transparent scorecard matching against target job descriptions.
4. **Milestone Career Roadmaps**: 12-week pedagogical skill roadmaps across 6 bi-weekly phases, project recommendations, and technical interview questions based on curated role taxonomies.
5. **Modern Responsive UI**: Clean, accessible, Tailwind CSS styled components with responsive mobile drawer, live health polling, and Dev User context switching.
6. **Strict User-Scoping Security**: Per-user resource isolation across all endpoints via `X-User-Id` header (HTTP 403 / 404 on cross-user access).
7. **Hardened API Contracts**: Uniform error envelopes, OpenAPI 3.x schema, Swagger UI (`/docs`), and ReDoc (`/redoc`).

---

## Quick Start

### 1. Run the Backend API
```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```
- API Health: `http://127.0.0.1:8000/api/health`
- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`

### 2. Run the Frontend Application
```powershell
cd frontend
npm install
npm run dev
```
- Application UI: `http://localhost:5173`

### 3. Run Test Suites & Verifications
```powershell
# Backend Test Suite (236 tests)
pytest -v

# Frontend Test Suite (19 tests)
cd frontend
npm test -- --run

# Frontend Production Build
npm run build

# Step 14 Security & E2E Verification Suite (23 gates)
cd ..
python scripts/verify_step14.py
```

---

## Documentation

- [System Architecture](docs/architecture.md)
- [Security Architecture & Audit](docs/security.md)
- [Production Readiness Guide](docs/production_readiness.md)
- [Production Deployment Guide](docs/deployment.md)
- [Architecture Decisions (ADRs)](docs/decisions.md)
- [Frontend Architecture](docs/frontend.md)
- [Frontend API Contract](docs/frontend_contract.md)
- [API Reference](docs/api.md)
- [Chat & Study Assistant Specification](docs/chat_study_assistant.md)
- [Resume Analyzer Specification](docs/resume_analyzer.md)
- [Career Roadmap Specification](docs/career_roadmap.md)

---

## License

This project is licensed under the MIT License.\n