# SahayakAI — System Architecture Specification

**Status:** ACTIVE  
**Version:** 1.0.0  
**Current Phase:** Completed STEP 4 (AI Provider Abstraction Layer)

---

## 1. System Overview

SahayakAI is an AI-powered academic and career mentorship assistant designed to deliver offline-capable document analysis, contextual study assistance, automated ATS resume evaluation, and personalized career roadmaps.

The platform is designed following strict layered architecture principles:
1. **Presentation Layer**: React Single Page Application (Vite + Tailwind CSS).
2. **API & Orchestration Layer**: FastAPI REST framework with centralized error handling, request validation, and CORS protection.
3. **Domain & Business Logic Layer**:
   - Ingestion & Extraction Services (PDF, TXT).
   - Local RAG Retrieval Engine (NumPy matrix operations, 384-dim embeddings).
   - Resume ATS Skill Gap Analyzer.
   - Dynamic Career Roadmap Synthesizer.
4. **AI Provider Abstraction Layer**: Generic `BaseAIProvider` decoupling domain logic from concrete LLMs (`DemoProvider`, `OpenAICompatibleProvider`, `GeminiProvider`).
5. **Persistence Layer**: SQLAlchemy 2.0 ORM with SQLite default storage (`data/sahayakai.db`) and strict referential integrity (`PRAGMA foreign_keys=ON`).

---

## 2. Multi-Tier Architecture Diagram

```mermaid
graph TD
    Client[Frontend: React / Vite / Tailwind SPA] -->|HTTP REST / JSON| API[FastAPI Application]

    subgraph FastAPI Framework [FastAPI Framework]
        API --> Middleware[CORS Middleware & Exception Handlers]
        Middleware --> Router[API Routers]
        Router --> HealthRoute["/api/health (Liveness & Health)"]
        Router --> DomainServices[Future Domain Services: RAG / Resume / Career]
    end

    subgraph AI Provider Abstraction [AI Provider Abstraction Layer (STEP 4)]
        DomainServices --> BaseProvider["BaseAIProvider (Interface)"]
        Factory["get_provider() Factory"] --> BaseProvider
        BaseProvider --> Demo["DemoProvider (Offline / Deterministic)"]
        BaseProvider --> OpenAI["OpenAICompatibleProvider (OpenAI / Ollama / vLLM)"]
        BaseProvider --> Gemini["GeminiProvider (Google GenAI SDK)"]
    end

    subgraph Persistence Layer [SQLAlchemy 2.0 Persistence (STEP 3)]
        DomainServices --> ORM[SQLAlchemy Session / Engine]
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

- **Database Models & Schemas**: Detailed in [`docs/database.md`](database.md).
- **Architecture Decision Records**: Documented in [`docs/decisions.md`](decisions.md).
- **Generative AI Providers**: Complete specification in [`docs/genai_providers.md`](genai_providers.md).
- **Architecture Freeze Baseline**: Verified in [`docs/architecture_freeze.md`](architecture_freeze.md).
