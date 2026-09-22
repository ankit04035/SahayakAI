# SahayakAI — Architecture Freeze Specification

## Status: FROZEN (Source of Truth)
**Version:** 1.1.0  
**Phase:** Phase 1 — Verification & Base Configuration  
**Architectural Baseline:** Approved

---

## 1. Problem Definition
Modern job seekers, early-career engineers, and students face severe challenges navigating career progression:
* **High Skill Mismatch & Unemployment**: Rapidly evolving industry requirements make traditional curricula obsolete, leaving candidates unprepared for market expectations.
* **Opaque Automated Screening (ATS)**: Over 75% of resumes are filtered out by Applicant Tracking Systems before reaching human recruiters due to poor formatting, missing domain keywords, or unquantified achievements.
* **Fragmented & Expensive Career Guidance**: Quality personalized mentorship is often inaccessible, gatekept behind expensive consulting fees, or scattered across disjointed blogs and job boards.
* **Lack of Actionable Roadmaps**: Candidates struggle to translate vague career goals (e.g., "Become an AI Engineer") into phased, measurable learning milestones with verified projects and resources.

**SahayakAI** addresses these challenges by providing an open, modular, intelligent assistant that automates resume analysis, generates custom milestone-based career roadmaps, and provides domain-grounded conversational mentorship through Retrieval-Augmented Generation (RAG).

---

## 2. Functional Requirements
* **FR-1: Safe Document Upload & Ingestion**:
  * Ingest resume files in `.pdf`, `.docx`, and `.txt` formats up to 10MB.
  * Extract clean, normalized plain text while isolating uploads in quarantined storage.
* **FR-2: Intelligent Resume Analysis**:
  * Extract structured entities: technical skills, soft skills, educational history, work experience, certifications.
  * Compute overall ATS readiness score and categorical sub-scores (format, keywords, experience impact, skill alignment).
  * Identify critical skill gaps against a user-specified or inferred target job role.
  * Generate actionable, prioritized improvement recommendations.
* **FR-3: Dynamic Career Roadmap Generator**:
  * Accept user profile, current proficiencies, target role, and desired timeframe.
  * Produce structured, phased milestone progression (e.g., Phase 1: Foundations [Month 1-2], Phase 2: Core Competencies & Projects [Month 3-4], Phase 3: Advanced Specialization & Portfolio [Month 5], Phase 4: Interview & Job Prep [Month 6]).
  * Suggest verified project ideas, industry tools, and key certification topics.
* **FR-4: Domain-Grounded Conversational RAG Engine**:
  * Answer user queries on career paths, interview prep, skill acquisition, and resume improvements.
  * Retrieve semantic context from a curated local knowledge base.
  * Provide grounded answers with citation references.
* **FR-5: Multi-Provider Generative AI Abstraction**:
  * Seamlessly toggle between OpenAI-compatible models, Google Gemini, and a deterministic offline Demo Mode.
  * Zero startup failure when API keys are absent.
* **FR-6: Multilingual Accessibility**:
  * Process resumes and queries in English and Hindi (Devanagari script support).
  * Provide prompt-level multilingual instruction handling.

---

## 3. Non-Functional Requirements
* **NFR-1: Performance & Latency**:
  * Non-LLM endpoints (file parsing, heuristic scoring, health checks) must respond in `< 500ms`.
  * RAG vector retrieval using local NumPy cosine similarity must complete in `< 50ms` for corpora under 10,000 chunks.
  * LLM streaming or single-pass responses must complete within `< 5s`.
* **NFR-2: Zero-Configuration Startup (Demo Mode)**:
  * The application must launch successfully without any API keys or network internet connectivity.
* **NFR-3: Security & Privacy**:
  * No secrets, tokens, or credentials checked into version control.
  * Uploaded documents stored locally with sanitized filenames and never exposed via public static routes.
* **NFR-4: Portability & Windows Reproducibility**:
  * Native, bug-free execution on Windows 10/11 environments using Python 3.10+ without requiring WSL, Docker, or native C compilation.
* **NFR-5: Maintainability & Extensibility**:
  * Strict separation of concerns (FastAPI routers -> Service layer -> Models/ML/RAG -> Providers).
  * Decoupled storage enabling transparent migration from SQLite to PostgreSQL.

---

## 4. System Architecture
SahayakAI employs a three-tier modular architecture designed for local execution and seamless cloud scalability:

```text
+-------------------------------------------------------------------------+
|                          Presentation Tier                              |
|          React + Vite Single-Page Application (Tailwind CSS)            |
|       [Dashboard]  [Resume Analyzer]  [Career Roadmap]  [RAG Chat]       |
+-------------------------------------------------------------------------+
                                    |
                                    | REST API / JSON (HTTP)
                                    v
+-------------------------------------------------------------------------+
|                           Application Tier                              |
|                           FastAPI Backend                               |
|   +-----------------------------------------------------------------+   |
|   | API Layer: /api/v1/ (routes/auth, resume, roadmap, chat, health)|   |
|   +-----------------------------------------------------------------+   |
|   | Service Layer: ResumeAnalyzer, RoadmapGenerator, RAGService     |   |
|   +-----------------------------------------------------------------+   |
|   | Domain Core: NLP Pipeline | Classical ML (scikit-learn)         |   |
|   |              Sentence-Transformers | Local NumPy Vector Retr.   |   |
|   +-----------------------------------------------------------------+   |
|   | Provider Adapter: DemoProvider | OpenAIProvider | GeminiProvider|   |
|   +-----------------------------------------------------------------+   |
+-------------------------------------------------------------------------+
                                    |
                                    v
+-------------------------------------------------------------------------+
|                        Data & Persistence Tier                          |
|  - SQLite Database (SQLAlchemy 2.0 ORM)                                 |
|  - Local Vector Cache (NumPy dense embeddings matrix: all-MiniLM-L6-v2) |
|  - Quarantined File Storage (uploads/)                                  |
+-------------------------------------------------------------------------+
```

---

## 5. Backend Architecture
The backend is structured around high-performance asynchronous FastAPI:
* **`app/routes/`**: Thin controller layer. Declares HTTP methods, routes, status codes, and delegates directly to services.
* **`app/services/`**: Business logic encapsulation. Orchestrates database transactions, ML inferences, and AI provider calls.
* **`app/models/`**: Declarative SQLAlchemy models representing persistent entities.
* **`app/schemas/`**: Pydantic v2 schemas enforcing request validation, input sanitization, and structured serialization.
* **`app/providers/`**: Pluggable AI integration layer implementing `BaseAIProvider`.
* **`app/nlp/`**: Text extraction, keyword matching, and taxonomy normalization.
* **`app/ml/`**: TF-IDF vectorization and classical scikit-learn classification models.
* **`app/rag/`**: Document chunking, transformer embedding generation, and cosine similarity vector retrieval.
* **`app/utils/`**: Cross-cutting utilities (file security, logging, error formatters).

---

## 6. Frontend Architecture
* **Technology Stack**: React 18+ bundled with Vite for near-instant hot-module reloading and optimized production bundles.
* **Styling**: Tailwind CSS for responsive, modern UI design.
* **Component Hierarchy**:
  * `App`: Layout wrapper with Navigation Bar, Theme context, and Provider notification banner (e.g., Demo Mode indicator).
  * `Dashboard`: High-level summary of analysis, active roadmaps, and quick action cards.
  * `ResumeAnalyzerView`: Drag-and-drop file upload zone, parsing status indicator, ATS score radar/breakdown, skill match badges, and improvement checklist.
  * `CareerRoadmapView`: Form for current skills and target role, interactive timeline with collapsible milestone cards, project ideas, and resource links.
  * `RAGChatView`: Conversational interface with markdown rendering, streaming support, and contextual source citation tags.
* **API Service Layer**: Centralized Axios/Fetch HTTP client configured with base URL, timeout handlers, and unified error interceptors.

---

## 7. Database Entities & Relationships
Persistence is managed via **SQLAlchemy 2.0** ORM targeting **SQLite** (`data/sahayak.db`):

```text
+-------------------+       1:N       +----------------------+
|       User        |---------------->|        Resume        |
|-------------------|                 |----------------------|
| id (PK)           |                 | id (PK)              |
| email (Unique)    |                 | user_id (FK -> User) |
| full_name         |                 | filename             |
| target_role       |                 | file_path            |
| experience_level  |                 | raw_text             |
| created_at        |                 | parsed_skills (JSON) |
+-------------------+                 | ats_score (Float)    |
         |                            | feedback_json (JSON) |
         | 1:N                        | created_at           |
         v                            +----------------------+
+------------------------+
|     CareerRoadmap      |
|------------------------|
| id (PK)                |
| user_id (FK -> User)   |
| current_role           |
| target_role            |
| timeline_months (Int)  |
| milestones_json (JSON) |
| recommended_skills     |
| created_at             |
+------------------------+
         |
         | 1:N
         v
+---------------------+       1:N       +----------------------+
|     ChatSession     |---------------->|     ChatMessage      |
|---------------------|                 |----------------------|
| id (PK)             |                 | id (PK)              |
| user_id (FK -> User)|                 | session_id (FK -> CS)|
| title               |                 | role (user/assistant)|
| created_at          |                 | content (Text)       |
+---------------------+                 | sources_json (JSON)  |
                                        | created_at           |
                                        +----------------------+
```

---

## 8. API Contract Strategy
* **Standard Envelope**: All endpoints return a predictable JSON payload:
  ```json
  {
    "success": true,
    "data": { ... },
    "error": null,
    "timestamp": "2026-09-22T16:40:00Z"
  }
  ```
* **Status Codes**: Strict HTTP semantics: `200 OK`, `201 Created`, `400 Bad Request`, `404 Not Found`, `422 Unprocessable Entity`, `500 Internal Server Error`.
* **Versioning**: URIs prefixed with `/api/v1/`.
* **Documentation**: OpenAPI 3.0 specs dynamically served via FastAPI Swagger UI at `/docs` and ReDoc at `/redoc`.

---

## 9. Document-Processing Pipeline
```text
Uploaded File (.pdf, .docx, .txt)
       |
       v
[Security Validation] ---> Check file size (<=10MB), sanitize filename, verify MIME type
       |
       v
[Quarantine Storage]  ---> Stored in uploads/ with UUID prefix (uploads/uuid_resume.pdf)
       |
       v
[Parser Dispatcher]   ---> PDF: pypdf text stream extraction
                           DOCX: python-docx paragraph and table extraction
                           TXT: UTF-8 safe text decoding with fallback
       |
       v
[Text Sanitization]   ---> Strip null bytes, normalize whitespace, remove unprintable chars
       |
       v
Clean Raw Text -> Passed to NLP Pipeline & Database
```

---

## 10. NLP Pipeline
* **Text Preprocessing**: Lowercasing, Unicode NFKD normalization, regex cleanup, punctuation handling, stopword filtering.
* **Section Segmentation**: Heuristic header classification targeting canonical sections (`Education`, `Experience`, `Skills`, `Projects`, `Certifications`).
* **Skill Extraction**: Hybrid extraction combining a comprehensive technical taxonomy dictionary (languages, frameworks, tools, soft skills) and n-gram keyword pattern matching.
* **Experience & Entity Extraction**: Regex and pattern-based duration calculators for work history, graduation dates, and degree levels.

---

## 11. Machine Learning Approach
* **Core Library**: `scikit-learn`.
* **Feature Extraction**: `TfidfVectorizer` (unigrams and bigrams, sublinear TF scaling, max 5,000 features).
* **Role Alignment & ATS Scoring**:
  * Classical `LogisticRegression` classifier trained/evaluated on job description matching to predict role-readiness.
  * TF-IDF cosine similarity between resume text vectors and target job description benchmark vectors.
* **Deterministic Baseline**: When untrained, heuristic rule-based scoring models provide consistent, auditable ATS scores from 0 to 100 based on weighted criteria (skill density, experience clarity, formatting cleanliness, impact verbs).

---

## 12. Deep-Learning / Transformer Embedding Approach
* **Framework**: `sentence-transformers`.
* **Model**: **`all-MiniLM-L6-v2`**:
  * Embedding Dimension: `384` dense floating-point values.
  * Model Size: `~80MB` (exceptionally lightweight, CPU-optimized).
  * Inference Latency: `< 20ms` per sentence on modern consumer CPUs.
  * Benchmark: Exceptional balance of speed and semantic retrieval accuracy on MTEB (Massive Text Embedding Benchmark).
* **Local Persistence**: Models cached locally in `models/` to ensure offline readiness after initial download.

---

## 13. RAG Architecture (Retrieval-Augmented Generation)
1. **Document Ingestion & Chunking**:
   * Knowledge base documents stored in `data/knowledge/`.
   * Recursive character text chunking:
     * `RAG_CHUNK_SIZE=500` (configurable via `.env`)
     * `RAG_CHUNK_OVERLAP=50` (configurable via `.env`)
2. **Embedding & Indexing**:
   * Chunks embedded via `all-MiniLM-L6-v2`.
   * Normalized vectors stored in a local **NumPy array matrix** (`shape: (N, 384)`).
3. **Retrieval**:
   * User query embedded to a `1x384` vector.
   * Cosine similarity computed via vectorized matrix dot product:
     $$\text{Similarity}(q, d_i) = q \cdot d_i$$ (since vectors are L2-normalized).
   * Filter chunks below `RAG_SIMILARITY_THRESHOLD=0.5` (configurable).
   * Return top-k matches (`RAG_TOP_K=4`, configurable).
4. **Augmentation & Generation**:
   * Retrieved context injected into the system prompt template.
   * Provider generates factual, grounded answers referencing retrieved context.

---

## 14. Generative AI Provider Abstraction
Decoupled multi-provider architecture managed via `BaseAIProvider`:
* **`BaseAIProvider`** (Abstract Base Class):
  * `generate_text(prompt: str, system_prompt: str = None) -> str`
  * `generate_chat(messages: List[Dict[str, str]]) -> str`
  * `is_available() -> bool`
* **Implementations**:
  1. `DemoProvider`: Offline heuristic generator providing deterministic, professional career and resume advice. Always available; requires zero external API keys.
  2. `OpenAIProvider`: Calls OpenAI API or OpenAI-compatible endpoints (Ollama, vLLM, LMStudio, Groq) using `httpx`.
  3. `GeminiProvider`: Calls Google Gemini API (`gemini-1.5-flash`).
* **Factory Selection**: Controlled via `DEFAULT_AI_PROVIDER` (`demo`, `openai`, `gemini`) in `.env`. Defaults gracefully to `DemoProvider` if keys are missing or provider fails.

---

## 15. Demo Mode
* **Zero API Key Guarantee**: The server starts and operates completely without requiring any external API keys or paid accounts.
* **Deterministic Responses**:
  * Resume Analysis: Produces complete skill breakdown, ATS scoring, and feedback using local NLP rules.
  * Career Roadmap: Generates comprehensive 4-phase milestone roadmaps based on pre-compiled domain trees.
  * RAG Assistant: Answers questions using local vector search over pre-indexed knowledge base documents and returns curated responses.
* **Client Transparency**: API responses in demo mode set `"is_demo": true` in response metadata.

---

## 16. Multilingual Support
* **Encoding**: Strict UTF-8 enforcement across all I/O streams, parsers, and database strings.
* **Languages Supported**: Primary support for English and Hindi (Devanagari script).
* **NLP & Tokenization**: Regex parsers handle Unicode ranges for Devanagari (`\u0900-\u097F`).
* **Prompt Strategy**: System prompt templates accept instructions to respond in the user's requested language.

---

## 17. Resume Analyzer Module
* **Inputs**: File upload (.pdf, .docx, .txt), optional target job title.
* **Processing**:
  1. Document parsing and plain-text extraction.
  2. NLP section classification (Skills, Experience, Education, Projects).
  3. Keyword and technical skill extraction.
  4. ATS Scoring formula:
     $$\text{ATS Score} = 0.35 \times S_{\text{skills}} + 0.30 \times S_{\text{experience}} + 0.20 \times S_{\text{format}} + 0.15 \times S_{\text{impact}}$$
  5. Gap analysis: Cross-reference extracted skills against required target skills.
* **Output**: Detailed scorecards, detected skills, missing skills, impact verb recommendations, and structured formatting advice.

---

## 18. Career Roadmap Module
* **Inputs**: Target role, current skills, experience level, available time commitment (months).
* **Processing**:
  1. Lookup skill requirements for target role from domain skill taxonomy.
  2. Compute differential gap between current skills and target skills.
  3. Partition gap into sequential pedagogical phases:
     * Phase 1: Foundational prerequisites and core concepts.
     * Phase 2: Applied development, tools, and hands-on projects.
     * Phase 3: Advanced architecture, specialization, and testing.
     * Phase 4: Portfolio building, mock interviews, and resume optimization.
* **Output**: Structured JSON roadmap containing milestones, weekly goals, project briefs, and curated learning links.

---

## 19. Security Requirements
* **No Hardcoded Secrets**: All secrets managed via `.env` and loaded via `pydantic-settings`.
* **Safe File Uploads**:
  * File size hard limit enforced before buffer read (default: 10MB).
  * Strict file extension allowlist (`.pdf`, `.docx`, `.txt`).
  * Filename sanitization: `pathlib.Path(filename).name` stripped and prepended with UUIDv4.
  * Path traversal prevention: Resolved target path must strictly reside within `uploads/`.
* **CORS Restrictions**: Origin whitelist loaded from `CORS_ORIGINS`.
* **SQL Injection Prevention**: Exclusive use of SQLAlchemy parameterized queries.
* **Input Validation**: Pydantic v2 schemas reject malformed or oversized JSON payloads.

---

## 20. Error Handling Strategy
* **Centralized FastAPI Exception Handlers**:
  * `RequestValidationError`: Formats Pydantic validation errors into readable field-level messages.
  * `HTTPException`: Standardized API error envelopes with HTTP status codes.
  * `Exception` (Catch-all): Logs stack traces internally while returning sanitized error messages to users.
* **Graceful Degradation**: If an external AI provider raises an HTTP timeout or rate-limit error, the provider adapter falls back to `DemoProvider` with an alert in the response.

---

## 21. Testing Strategy
* **Unit Tests (`tests/unit/`)**:
  * Document text extraction (`pypdf`, `python-docx`).
  * NLP skill extractor and stopword filters.
  * TF-IDF vectorization and scoring logic.
  * Recursive chunking and cosine similarity retrieval.
  * AI Provider interface and DemoProvider output validation.
* **Integration Tests (`tests/integration/`)**:
  * FastAPI route execution via `TestClient`.
  * File upload endpoints with mock files.
  * Database CRUD operations using temporary in-memory SQLite (`sqlite:///:memory:`).
* **End-to-End Tests (`tests/e2e/`)**:
  * Full workflow: Upload sample resume -> trigger analysis -> verify ATS score and roadmap generation in Demo Mode.

---

## 22. Dependency Strategy
* **Minimalist Core**: Dependencies restricted strictly to libraries essential for the frozen architecture.
* **Dependencies**:
  * Web / API: `fastapi`, `uvicorn[standard]`, `pydantic`, `pydantic-settings`, `python-dotenv`, `python-multipart`, `httpx`
  * Database: `sqlalchemy`
  * ML / NLP: `numpy`, `scikit-learn`, `sentence-transformers`
  * Document Extraction: `pypdf`, `python-docx`
  * Testing: `pytest`, `pytest-asyncio`
* **Avoidance of Heavy Bloat**: No heavy distributed vector databases (Milvus, Pinecone) or bulky monolithic frameworks (LangChain / LlamaIndex core) for the base version; all vector search operations are self-contained.

---

## 23. Windows Reproducibility
* **Cross-Platform File Paths**: All paths constructed using `pathlib.Path`. No hardcoded forward slashes or backslashes.
* **Virtual Environment**: Standard PowerShell activation instructions (`.venv\Scripts\Activate.ps1`).
* **Encoding**: All file readers and writers explicitly pass `encoding="utf-8"`.
* **No POSIX-Only Tools**: Avoidance of Unix-specific commands (`grep`, `curl`, `chmod`) in application scripts.

---

## 24. Implementation Phases
* **Phase 1 (Current)**: Repository Scaffold, Architecture Freeze Verification & Base Configuration.
* **Phase 2**: Core Database Models (SQLAlchemy), Database Initialization & Pydantic Schemas.
* **Phase 3**: AI Provider Abstraction Layer & Deterministic Demo Mode Engine.
* **Phase 4**: Document Ingestion Service, NLP Text Processing & Resume Analyzer Engine.
* **Phase 5**: RAG Engine with NumPy Cosine Similarity & Knowledge Base Indexer.
* **Phase 6**: Dynamic Career Roadmap Generation Service.
* **Phase 7**: FastAPI REST Endpoints, Centralized Exception Handlers & Verification Tests.
* **Phase 8**: Frontend Single Page Application (React + Vite + Tailwind CSS).
* **Phase 9**: End-to-End System Integration, Verification & Documentation Wrap-up.

---

## 25. Known Risks & Mitigations
| # | Risk Description | Severity | Mitigation Strategy |
| :--- | :--- | :--- | :--- |
| 1 | External LLM API rate limits, costs, or downtime | High | Automatic fallback to `DemoProvider`; local caching of repeated prompts. |
| 2 | Unstructured, non-standard resume formats failing extraction | Medium | Dual-engine parsing (`pypdf` + `python-docx`), text sanitization, heuristic fallbacks. |
| 3 | Memory overhead from large embedding models | Medium | Selection of `all-MiniLM-L6-v2` (only ~80MB); lazy loading on first inference. |
| 4 | First-run startup failures due to missing configuration | High | Default `.env.example` configured to `DEFAULT_AI_PROVIDER=demo`, requiring zero keys. |
| 5 | Windows file permission or encoding errors | Low | Strict `pathlib.Path` usage and explicit `encoding="utf-8"` on all operations. |
