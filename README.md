# SahayakAI

SahayakAI is an intelligent career guidance and productivity assistant built to empower learners, job-seekers, and working professionals with automated resume analysis, personalized career roadmap generation, domain-grounded conversational intelligence via Retrieval-Augmented Generation (RAG), and curated learning recommendations. Designed with a modular, enterprise-ready architecture, SahayakAI leverages FastAPI for high-performance backend serving, pluggable LLM provider adapters, and localized data processing to deliver contextual, actionable insights.

---

## Current Project Status

**Current Phase:** Phase 4 — AI Provider Abstraction Layer & Deterministic Demo Mode  
The repository has established:
1. Architecture Freeze baseline specifications ([`docs/architecture_freeze.md`](docs/architecture_freeze.md)).
2. Complete FastAPI backend foundation with centralized error handling and health checks.
3. Complete SQLAlchemy 2.0 ORM persistence layer with 9 models, UTC timestamps, and cascading delete rules ([`docs/database.md`](docs/database.md)).
4. Pluggable, vendor-neutral GenAI Provider Abstraction Layer supporting zero-key deterministic Demo Mode, OpenAI-compatible endpoints, and Google Gemini with defensive secret sanitization ([`docs/genai_providers.md`](docs/genai_providers.md)).

---

## Planned Modules

1. **FastAPI Application Backend (`backend/app/routes/`, `backend/app/services/`)**:
   High-throughput asynchronous REST API providing validation, orchestration, and request lifecycle management.

2. **Resume Analyzer (`backend/app/nlp/`, `backend/app/services/`)**:
   Document ingestion engine extracting structured skills, experience history, and candidate profiles from PDF/DOCX files with scoring and feedback metrics.

3. **Career Roadmap Generator (`backend/app/services/`, `backend/app/ml/`)**:
   AI-driven progression model mapping out milestone-based skill acquisition and career advancement strategies based on user goals and industry requirements.

4. **RAG Knowledge Base Assistant (`backend/app/rag/`, `backend/app/providers/`)**:
   Retrieval-Augmented Generation engine combining localized vector similarity search with language models to deliver accurate, grounded domain Q&A.

5. **AI Provider Adapters (`backend/app/providers/`)**:
   Unified provider abstraction supporting OpenAI, Google Gemini, Hugging Face, and local models.

6. **Frontend Interface (`frontend/`)**:
   Modern, responsive user interface for document uploads, interactive roadmap visualization, and conversational assistance.

---

## Basic Directory Structure

```text
SahayakAI/
├── README.md
├── .env.example
├── .gitignore
├── requirements.txt
├── backend/
│   └── app/
│       ├── __init__.py
│       ├── models/
│       ├── schemas/
│       ├── routes/
│       ├── services/
│       ├── ml/
│       ├── nlp/
│       ├── rag/
│       ├── providers/
│       └── utils/
├── frontend/
├── tests/
├── scripts/
├── docs/
├── data/
├── models/
└── uploads/
```

### Directory Roles & Responsibilities

| Directory / File | Description |
| :--- | :--- |
| `README.md` | Project overview, architectural documentation, and usage instructions |
| `.env.example` | Environment variable template with documented placeholders |
| `.gitignore` | Security-hardened exclusions for secrets, venvs, caches, and datasets |
| `requirements.txt` | Minimal dependencies pinned to core architectural requirements |
| `backend/app/models/` | Domain entities and database schema models |
| `backend/app/schemas/` | Pydantic schemas for request validation and serialization |
| `backend/app/routes/` | FastAPI endpoint routers and API controllers |
| `backend/app/services/` | Business logic services and cross-module workflows |
| `backend/app/ml/` | Machine learning model loaders, inference pipelines, and trainers |
| `backend/app/nlp/` | Natural language processing, tokenization, and resume parsing |
| `backend/app/rag/` | RAG retrieval, vector search, chunking, and document indexing |
| `backend/app/providers/`| Pluggable multi-provider LLM adapters (Demo, OpenAI, Gemini) |
| `backend/app/utils/` | Shared utilities, logging configuration, and helpers |
| `frontend/` | Client-side user interface source code |
| `tests/` | Unit, integration, and end-to-end automated test suites |
| `scripts/` | Automation, data preparation, and maintenance utilities |
| `docs/` | Architecture freeze specifications and technical guides |
| `data/` | Local datasets and vector store indices (git-ignored) |
| `models/` | Saved model weights, caches, and checkpoints (git-ignored) |
| `uploads/` | Ephemeral uploaded documents and resumes (git-ignored) |

---

## Getting Started

### 1. Prerequisites
* Python 3.10+ (Recommended: Python 3.12)
* Git

### 2. Environment Setup
Create and activate a virtual environment:
```bash
# Windows (PowerShell)
python -m venv .venv
.venv\Scripts\Activate.ps1

# Linux / macOS
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Copy `.env.example` to `.env` and adjust configuration:
```bash
# Windows
Copy-Item .env.example .env

# Linux / macOS
cp .env.example .env
```

*Note: By default, `AI_PROVIDER=demo` is configured, allowing the entire application and test suite to run without any external API keys or cloud accounts.*

### 5. Run the Server
```bash
python -m uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
```
Verify health status at `http://127.0.0.1:8000/api/health`.

### 6. Run Automated Tests
```bash
python -m pytest -v
```
