# SahayakAI — System Architecture Specification

**Status:** ACTIVE  
**Version:** 1.2.0  
**Current Phase:** Completed STEP 9 (Resume Analyzer & ATS Scorecard)

---

## 1. System Overview

SahayakAI is an AI-powered academic and career mentorship assistant designed to deliver offline-capable document analysis, contextual study assistance, automated ATS resume evaluation, and personalized career roadmaps.

The platform is designed following strict layered architecture principles:
1. **Presentation Layer**: React Single Page Application (Vite + Tailwind CSS).
2. **API & Orchestration Layer**: FastAPI REST framework with centralized error handling, request validation, CORS protection, and routers (`/api/health`, `/api/documents`).
3. **Domain & Business Logic Layer**:
   - Ingestion & Extraction Services (`backend/app/services/document_service.py` via PyMuPDF and UTF-8 multi-encoding decoding).
   - Core NLP Engine (`backend/app/nlp/` — deterministic text cleaner, reading statistics, script-based language identification, multilingual keyword extraction, query preprocessor, boundary-aware sliding window chunker).
   - Embedding & Transformer Engine (`backend/app/rag/` — `all-MiniLM-L6-v2` 384-dimensional sentence-transformers, L2 normalization, in-process model caching, batch encoding, JSON vector persistence).
   - Local RAG Retrieval Engine (STEP 7 Completed — NumPy dot product, cosine similarity search, threshold gating).
   - Study Assistant & Grounded Chat Service (STEP 8 Completed — multi-turn dialogue, bounded history, citation tracking).
   - Resume ATS Skill Gap Analyzer (STEP 9 Completed — structured parsing, taxonomy normalization, transparent scoring).
   - Dynamic Career Roadmap Synthesizer (Future STEP 9).
4. **AI Provider Abstraction Layer**: Generic `BaseAIProvider` decoupling domain logic from concrete LLMs (`DemoProvider`, `OpenAICompatibleProvider`, `GeminiProvider`).
5. **Persistence Layer**: SQLAlchemy 2.0 ORM with SQLite default storage (`data/sahayakai.db`) and strict referential integrity (`PRAGMA foreign_keys=ON`).

---

## 2. Multi-Tier Architecture Diagram

```mermaid
graph TD
    Client[Frontend: React / Vite / Tailwind SPA] -->|HTTP REST / JSON / Multipart| API[FastAPI Application]

    subgraph FastAPI Framework [FastAPI Framework]
        API --> Middleware[CORS Middleware & Exception Handlers]
        Middleware --> Router[API Routers]
        Router --> HealthRoute["/api/health (Liveness & Health)"]
        Router --> DocRoute["/api/documents (Upload, Detail, Chunks)"]
    end

    subgraph Document & NLP Pipeline [Document Processing & Core NLP (STEP 5)]
        DocRoute --> DocService["DocumentService (Upload & Orchestration)"]
        DocService --> FileVal["file_validation & filename (Security)"]
        DocService --> Storage["Disk Storage: uploads/"]
        DocService --> Extractor["Text Extraction: PyMuPDF / Text Decoder"]
        DocService --> NLPCleaner["NLP Text Cleaner (Unicode NFC / Hyphens)"]
        DocService --> NLPStats["Document Statistics & Language Detection"]
        DocService --> NLPKeywords["Multilingual Keyword Extractor"]
        DocService --> NLPChunker["Boundary-Aware Document Chunker"]
    end

    subgraph AI Provider Abstraction [AI Provider Abstraction Layer (STEP 4)]
        DocService -.->|Future RAG| BaseProvider["BaseAIProvider (Interface)"]
        Factory["get_provider() Factory"] --> BaseProvider
        BaseProvider --> Demo["DemoProvider (Offline / Deterministic)"]
        BaseProvider --> OpenAI["OpenAICompatibleProvider (OpenAI / Ollama / vLLM)"]
        BaseProvider --> Gemini["GeminiProvider (Google GenAI SDK)"]
    end

    subgraph Persistence Layer [SQLAlchemy 2.0 Persistence (STEP 3)]
        DocService --> ORM[SQLAlchemy Session / Engine]
        ORM --> DB[(SQLite / PostgreSQL Database)]
        DB --- U[users]
        DB --- D[documents]
        DB --- DC[document_chunks]
        DB --- CS[chat_sessions]
        DB --- CM[chat_messages]
        DB --- R[resumes]
        DB --- RA[resume_analyses]
        DB --- CP[career_profiles]
        DB --- RM[roadmaps]
    end
```

---

## 3. Subsystem References

- **Sentence-Embedding Pipeline**: Complete specification in [`docs/embedding_pipeline.md`](embedding_pipeline.md).
- **RAG Architecture**: RAG retrieval roadmap in [`docs/rag.md`](rag.md).
- **Document Processing**: Complete specification in [`docs/document_processing.md`](document_processing.md).
- **Core NLP Pipeline**: Detailed algorithms and models in [`docs/nlp_pipeline.md`](nlp_pipeline.md).
- **Database Models & Schemas**: Detailed in [`docs/database.md`](database.md).
- **Architecture Decision Records**: Documented in [`docs/decisions.md`](decisions.md).
- **Generative AI Providers**: Complete specification in [`docs/genai_providers.md`](genai_providers.md).
- **Architecture Freeze Baseline**: Verified in [`docs/architecture_freeze.md`](architecture_freeze.md).

- **Resume Analyzer**: Detailed architecture and ATS scoring formulas in [`docs/resume_analyzer.md`](resume_analyzer.md).
