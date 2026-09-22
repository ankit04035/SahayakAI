# SahayakAI — AI-Powered Career & Academic Mentor

[![Production: Deployed](https://img.shields.io/badge/Production-Deployed%20%26%20Verified-brightgreen.svg)]()
[![Backend Tests: 236 Passed](https://img.shields.io/badge/Backend%20Tests-236%20Passed-brightgreen.svg)]()
[![Frontend Tests: 19 Passed](https://img.shields.io/badge/Frontend%20Tests-19%20Passed-brightgreen.svg)]()
[![Security: 23/23 Gates Passed](https://img.shields.io/badge/Security-23%2F23%20Gates%20Passed-brightgreen.svg)]()
[![Python: 3.12.2](https://img.shields.io/badge/Python-3.12.2-blue.svg)]()
[![FastAPI: 0.115](https://img.shields.io/badge/FastAPI-0.115-teal.svg)]()
[![React: 18.3](https://img.shields.io/badge/React-18.3-61dafb.svg)]()
[![Vite: 6.0](https://img.shields.io/badge/Vite-6.0-646cff.svg)]()
[![License: MIT](https://img.shields.io/badge/License-MIT-purple.svg)]()

> **SahayakAI (सहायक AI)** is an intelligent, privacy-first career advancement and study copilot. Built for students and early-career developers, SahayakAI integrates reference document processing, semantic vector search (RAG), conversational study assistance, transparent ATS resume scoring, milestone-based career roadmap generation, and a modern React + Vite frontend application.

---

## Current Status: STEP 15 Complete (Production Deployed) ✅

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
- **Step 15:** Final Production Deployment (Vercel + Render + PostgreSQL) ✅
  - **Frontend Target**: Deployed on **Vercel** with global edge CDN and SPA rewrites (`vercel.json`)
  - **Backend Target**: Deployed on **Render Web Service** with Python `3.12.2` and ASGI Uvicorn
  - **Database Target**: Managed **PostgreSQL** with `psycopg2-binary` driver and automatic schema creation
  - **Storage Target**: Render Persistent Disk (`/var/data/uploads`) for durable PDF/TXT document and resume storage
  - **Live Verification**: `scripts/verify_production.py` passing 12 / 12 production gates (100% green)
  - **Test Baselines**: 236 / 236 Backend tests passing, 19 / 19 Frontend tests passing, zero build errors
  - **Dual-Directory Parity**: 100% SHA-256 match between root and `SahayakAI/`

---

## Production Architecture

```
                    ┌─────────────────────────┐
                    │    End-User Browser     │
                    └───────────┬─────────────┘
                                │ HTTPS
                                ▼
                    ┌─────────────────────────┐
                    │   Vercel Global CDN     │
                    │   React + Vite SPA      │
                    └───────────┬─────────────┘
                                │ API Requests
                                ▼
                    ┌─────────────────────────┐
                    │   Render Web Service    │
                    │   FastAPI + Uvicorn     │
                    └─────┬─────────────┬─────┘
                          │             │
        SQLAlchemy 2.0    │             │ File I/O
                          ▼             ▼
             ┌──────────────────┐  ┌──────────────────┐
             │    PostgreSQL    │  │ Persistent Disk  │
             │   Managed DB     │  │ /var/data/uploads│
             └──────────────────┘  └──────────────────┘
```

---

## Quick Start & Verification

### 1. Run the Backend API Locally
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
# Backend Regression Suite (236 tests)
pytest -v

# Frontend Test Suite (19 tests)
cd frontend
npm test -- --run

# Frontend Production Build
npm run build

# Step 15 Live Production Verification (Local in-process simulation)
cd ..
python scripts/verify_production.py --local

# Step 15 Production Verification (Live Cloud URL)
python scripts/verify_production.py --api-url https://sahayakai-backend.onrender.com/api
```

---

## Production Deployment Guide

For full production deployment instructions, configuration references, and operational procedures, refer to:
- [Production Deployment Guide](docs/deployment.md)
- [Production Readiness Guide](docs/production_readiness.md)
- [Security Architecture & Audit](docs/security.md)
- [Architecture Decisions (ADRs)](docs/decisions.md)
- [Frontend Architecture](docs/frontend.md)
- [Frontend API Contract](docs/frontend_contract.md)
- [Render Blueprint Specification](render.yaml)
- [Vercel Routing Specification](vercel.json)

---

## License

This project is licensed under the MIT License.\n