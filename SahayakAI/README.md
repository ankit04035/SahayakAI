# SahayakAI — AI-Powered Career & Academic Mentor

[![Tests: 236 Backend Passed](https://img.shields.io/badge/Backend%20Tests-236%20Passed-brightgreen.svg)]()
[![Tests: 19 Frontend Passed](https://img.shields.io/badge/Frontend%20Tests-19%20Passed-brightgreen.svg)]()
[![Python: 3.12](https://img.shields.io/badge/Python-3.12-blue.svg)]()
[![FastAPI: 0.115](https://img.shields.io/badge/FastAPI-0.115-teal.svg)]()
[![React: 18.3](https://img.shields.io/badge/React-18.3-61dafb.svg)]()
[![Vite: 6.0](https://img.shields.io/badge/Vite-6.0-646cff.svg)]()
[![License: MIT](https://img.shields.io/badge/License-MIT-purple.svg)]()

> **SahayakAI (सहायक AI)** is an intelligent, offline-capable, and privacy-first career advancement and study copilot. Built for students and early-career developers, SahayakAI integrates reference document processing, semantic vector search (RAG), conversational study assistance, transparent ATS resume scoring, milestone-based career roadmap generation, and a modern React + Vite frontend application.

---

## Current Status: STEP 13 Complete ✅

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
  - **Connected React Frontend with FastAPI Backend over HTTP & CORS**
  - **Verified Workflows A–E**: Study Documents, Multi-Turn Chat, ATS Resume Analyzer, Career Profile, and 12-Week Roadmap
  - **Cross-User Scoping Verified**: User 1 vs User 2 isolation enforced via `X-User-Id`
  - **Live Verification Script**: `scripts/verify_step13.py` passing 9/9 integration steps
  - **Frontend Tests**: 19 / 19 Vitest tests passing (100% green across 4 test suites)
  - **Backend Regression Tests**: 236 / 236 pytest tests passing (100% green)
  - **Production Build**: Zero-error Vite production build (`npm run build`)
  - **Security Audit**: Zero hardcoded provider secrets or API keys in frontend bundles
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
API docs will be available at:
- Swagger: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### 2. Run the Frontend Application
```powershell
cd frontend
npm install
npm run dev
```
Open `http://localhost:5173` in your browser.

### 3. Run End-to-End Integration Verification
```powershell
python scripts/verify_step13.py
```

### 4. Run Backend Test Suite
```powershell
python -m pytest -v
```
*(All 236 tests pass in ~35 seconds on standard CPU)*

### 5. Run Frontend Test Suite
```powershell
cd frontend
npm test
```
*(All 19 tests pass)*

### 6. Build Frontend for Production
```powershell
cd frontend
npm run build
```

---

## Architecture Documentation

- [Frontend Architecture & Contract Integration](docs/frontend.md)
- [Frontend API Contract](docs/frontend_contract.md)
- [Architecture Freeze](docs/architecture_freeze.md)
- [API Reference](docs/api_reference.md)
- [Demo Mode Specification](docs/demo_mode.md)

---

## License

MIT License — Built for academic and career advancement.
