# SahayakAI - Architecture Freeze Specification

## Status: FROZEN (Source of Truth)
**Version:** 1.0.0  
**Phase:** Phase 1 (Scaffold & Base Configuration)

---

## 1. Executive Overview

SahayakAI is an AI-powered career guidance and productivity assistant designed to empower users with intelligent resume analysis, personalized career roadmapping, contextual conversational assistance (RAG), and tailored skill recommendations.

This document serves as the formal **Architecture Freeze** record and the single source of truth for module boundaries, package hierarchies, and architectural constraints.

---

## 2. System Architecture & Module Boundaries

The project architecture enforces strict separation of concerns across the following layers:

### 2.1 Backend Package Layout (`backend/app/`)
* **`models/`**: Database models and domain entities.
* **`schemas/`**: Pydantic data schemas for request validation and response serialization.
* **`routes/`**: FastAPI API routers and HTTP endpoint controllers.
* **`services/`**: Application business logic, orchestrating workflows between domain models, ML pipelines, and AI providers.
* **`ml/`**: Machine learning model definitions, training routines, and inference pipelines.
* **`nlp/`**: Natural language processing routines, text extraction, resume parsing, and tokenization.
* **`rag/`**: Retrieval-Augmented Generation components, including document loaders, text chunkers, embedding managers, and vector store retrieval.
* **`providers/`**: Pluggable provider adapter layer for external LLMs and cloud AI services (OpenAI, Google Gemini, Hugging Face, local engines).
* **`utils/`**: Shared helper utilities, logging setup, security utilities, and common file handlers.

### 2.2 Complementary Top-Level Modules
* **`frontend/`**: Client application interface.
* **`tests/`**: Automated unit, integration, and regression test suites.
* **`scripts/`**: Development automation, data ingestion, and migration scripts.
* **`docs/`**: Project architecture, API documentation, and specifications.
* **`data/`**: Local datasets, sample inputs, and vector store indices (git-ignored).
* **`models/`**: Local model weights, fine-tuned checkpoints, and serialized estimators (git-ignored).
* **`uploads/`**: Ephemeral storage for uploaded resumes and documents (git-ignored).

---

## 3. Planned Functional Modules

1. **Resume Analyzer**:
   * Accepts resume files (PDF, DOCX).
   * Extracts structured entities (skills, experience, education).
   * Generates analytical feedback and scorecards.

2. **Career Roadmap Generator**:
   * Generates step-by-step career progression milestones based on current qualifications and target career roles.

3. **RAG Knowledge Base Engine**:
   * Ingests career documents, market insights, and educational resources into a vector store.
   * Performs semantic similarity retrieval to ground LLM responses with factual, up-to-date context.

4. **Multi-Provider AI Layer**:
   * Abstracted interface for switching between OpenAI, Gemini, HuggingFace, or local models via `.env` configuration.

---

## 4. Architectural Rules & Constraints

* **Strict Decoupling**: API routers must never contain heavy business logic; routes delegate to `services/`.
* **Zero Secret Leakage**: No credentials, API keys, or environment-specific values may be hardcoded. All settings are read via `pydantic-settings` from `.env`.
* **Clean Scaffold Rule**: In Phase 1, only directory scaffolding, package `__init__.py` markers, and baseline configuration files are created. Application business logic, fake APIs, and feature implementations remain deferred to their dedicated development phases.
