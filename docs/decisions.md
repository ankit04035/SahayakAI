# SahayakAI — Architecture Decision Records (ADRs)

**Status:** APPROVED  
**Baseline Date:** 2026-09-22  
**Context:** Repository Scaffold & Architecture Freeze Verification

---

## ADR-01: SQLite as the Initial Database

### Context
SahayakAI requires a reliable, lightweight persistence store for user sessions, uploaded resume metadata, ATS evaluation results, and generated career roadmaps.

### Decision
Use **SQLite** via **SQLAlchemy 2.0 ORM** as the default initial database engine (`data/sahayak.db`).

### Rationale
1. **Zero-Configuration & Portability**: SQLite requires no separate background server process, external port configuration, or daemon setup. This makes developer onboarding and evaluation on local Windows machines instant and reliable.
2. **ACID Compliance & Reliability**: SQLite provides full ACID transaction guarantees suitable for local single-user or small-team evaluation workflows.
3. **Seamless Migration Path**: By leveraging SQLAlchemy 2.0 declarative models, the entire data layer remains decoupled from SQLite-specific dialects. Migrating to PostgreSQL or MySQL in production requires modifying only the `DATABASE_URL` connection string with zero changes to business logic or service code.
4. **Self-Contained Artifact**: The database file is located in `data/sahayak.db` (git-ignored), facilitating easy backups, resets, and isolated test suites.

---

## ADR-02: Local Cosine-Similarity Vector Retrieval via NumPy

### Context
The RAG (Retrieval-Augmented Generation) knowledge engine requires semantic similarity search over pre-processed text chunks representing career paths, course guides, and domain FAQs.

### Decision
Implement vector retrieval initially using **NumPy matrix multiplication / cosine similarity** over in-memory L2-normalized dense embedding arrays rather than introducing a heavy vector database daemon (such as Milvus, Qdrant, or Pinecone).

### Rationale
1. **Simplicity and Zero External Dependencies**: Eliminates complex Docker setups, background services, and C++ binary compilation challenges on Windows.
2. **Deterministic & Blazing Fast for Targeted Corpora**: For a curated career guidance corpus of 500 to 10,000 chunks, a vectorized NumPy dot product across 384-dimensional embeddings takes `< 15 milliseconds` on modern CPUs, outperforming network round-trip latencies of remote vector databases.
3. **Full Auditability**: Distance calculations, score thresholds, and top-k filtering are directly inspectable in clean Python code without opaque black-box indexing.
4. **Future-Proof Interface**: The RAG retrieval interface is encapsulated behind a `VectorStore` adapter, allowing drop-in upgrades to persistent vector databases (e.g., ChromaDB or pgvector) when corpora exceed 50,000 documents.

---

## ADR-03: Selection of `all-MiniLM-L6-v2` as the Embedding Model

### Context
Semantic search, resume-to-job matching, and RAG retrieval require dense vector representations of textual content.

### Decision
Adopt **`sentence-transformers/all-MiniLM-L6-v2`** as the default embedding model.

### Rationale
1. **Compact Model Footprint**: At only `~80MB` on disk, the model downloads quickly and fits comfortably in memory without requiring dedicated GPU hardware.
2. **High CPU Throughput**: Generates embeddings in `< 20ms` per sentence on standard consumer CPUs, crucial for responsive Windows local execution.
3. **Proven Benchmark Quality**: Evaluated on the Massive Text Embedding Benchmark (MTEB), `all-MiniLM-L6-v2` delivers state-of-the-art sentence semantic similarity relative to its diminutive parameter count.
4. **Dimension Efficiency**: Produces `384`-dimensional embeddings, keeping in-memory NumPy matrix operations lean and memory consumption negligible.

---

## ADR-04: Pluggable Generative AI Provider Abstraction Layer

### Context
SahayakAI relies on generative language models for resume feedback generation, career advice synthesis, and conversational RAG responses. Relying on a single proprietary vendor creates vendor lock-in, testing friction, and runtime vulnerability.

### Decision
Establish an abstract base provider interface (**`BaseAIProvider`**) with concrete adapters for:
* `DemoProvider` (deterministic local heuristics, zero keys)
* `OpenAIProvider` (OpenAI API and OpenAI-compatible endpoints like Ollama, Groq, vLLM)
* `GeminiProvider` (Google Gemini 1.5 Flash / Pro)

### Rationale
1. **Vendor Independence**: Allows developers and end-users to swap LLM backends simply by updating `DEFAULT_AI_PROVIDER` in `.env`.
2. **Local Model & OpenAI Compatibility**: Organizations running self-hosted models (via Ollama, vLLM, or LMStudio) can utilize the OpenAI-compatible adapter without modifying backend code.
3. **Resilience & Fallback**: If an external provider encounters rate limits, billing caps, or network outages, the system can gracefully fall back to alternative providers or Demo Mode.

---

## ADR-05: Mandatory Zero-Key Demo Mode

### Context
New contributors, evaluators, and automated test runners often lack active API keys for proprietary LLMs (e.g., OpenAI or Google Gemini). First-run crashes due to missing credentials create immediate friction.

### Decision
Make **Demo Mode** a first-class, default architectural requirement. The application must start and execute all core workflows without any API keys or internet connection.

### Rationale
1. **Immediate Out-of-the-Box Evaluation**: Evaluators can clone the repository, run `uvicorn backend.app.main:app`, and test resume analysis, roadmap generation, and RAG Q&A immediately.
2. **Zero Financial Cost for Testing**: Unit, integration, and UI component tests execute against deterministic local logic without burning API credits.
3. **Predictable CI/CD Pipelines**: Automated test harnesses pass consistently without flaky network timeouts or external rate limits.
4. **User Transparency**: All responses generated under Demo Mode explicitly flag `"is_demo": true` in the API payload metadata.

---

## ADR-06: Phased Feature Development

### Context
Developing a complex AI application involving multi-modal parsers, NLP pipelines, vector stores, ORMs, and multi-provider LLMs simultaneously creates high risk of architectural drift, debugging ambiguity, and regression.

### Decision
Enforce a strict **9-Phase Sequential Implementation Workflow**:
1. Phase 1: Repository Scaffold, Architecture Freeze & Base Configuration.
2. Phase 2: Core Database Models (SQLAlchemy), Database Initialization & Pydantic Schemas.
3. Phase 3: AI Provider Abstraction Layer & Deterministic Demo Mode Engine.
4. Phase 4: Document Ingestion Service, NLP Text Processing & Resume Analyzer Engine.
5. Phase 5: RAG Engine with NumPy Cosine Similarity & Knowledge Base Indexer.
6. Phase 6: Dynamic Career Roadmap Generation Service.
7. Phase 7: FastAPI REST Endpoints, Centralized Exception Handlers & Verification Tests.
8. Phase 8: Frontend Single Page Application (React + Vite + Tailwind CSS).
9. Phase 9: End-to-End System Integration, Verification & Documentation Wrap-up.

### Rationale
1. **Verifiable Milestones**: Each layer is built, type-checked, and unit-tested in isolation before higher-level modules depend on it.
2. **Preservation of Architectural Integrity**: Prevents premature feature coupling (e.g., writing API routes before domain schemas are settled).
3. **Traceable Debugging**: Isolates failures directly to the active phase rather than diagnosing sprawling cross-layer bugs.

---

## ADR-07: JSON Float List Storage for Document Chunk Vector Embeddings

### Context
SahayakAI requires persistent storage for text chunk vector embeddings generated during document ingestion for semantic search and RAG retrieval. Introducing an external vector database (such as Milvus, ChromaDB, or pgvector) at this stage introduces native C++ compilation dependencies, Docker requirements, and cross-platform installation friction on Windows.

### Decision
Store vector embeddings directly within the `document_chunks` table as a `JSON` column containing a serialized array of floating-point numbers (e.g. `[0.0123, -0.0456, ...]`). Semantic similarity search will deserialize these arrays and execute vectorized cosine similarity via NumPy matrix multiplication in memory.

### Rationale
1. **Zero External Infrastructure**: SQLite stores JSON natively without requiring additional database extensions, separate daemon processes, or cloud vector database accounts.
2. **Deterministic Windows Compatibility**: Completely bypasses binary wheel compilation issues with native C++ vector libraries (e.g., hnswlib, chromadb) on Windows.
3. **High Performance for Target Corpora**: For knowledge bases ranging up to 10,000 chunks, batch deserialization and NumPy in-memory dot product takes `< 15ms`, well within interactive RAG latency budgets.
4. **Seamless Future Migration**: When corpora exceed in-memory scale, the database column can be easily migrated to `pgvector` (`vector(384)`) or indexed via external vector stores without changing chunk identification or metadata schemas.

---

## ADR-08: Explicit Cascading Deletion Hierarchy and Orphan Removal

### Context
The relational data model contains hierarchical dependencies: users own documents, resumes, chat sessions, and career profiles. In turn, documents own chunks, chat sessions own messages, resumes own analyses, and career profiles own roadmaps. Uncontrolled or implicit deletions risk orphaned records and foreign key constraint violations.

### Decision
Implement explicit cascading deletion (`cascade="all, delete-orphan"`, `passive_deletes=True`) on all parent-to-child entity relationships, paired with database-level `ON DELETE CASCADE` foreign key clauses, and enforce SQLite foreign key integrity via `PRAGMA foreign_keys=ON` on every database connection. For the loose reference between `ChatSession` and `Document`, apply `ON DELETE SET NULL`.

### Rationale
1. **Data Integrity**: Deleting a user cleanly purges all associated documents, vectorized chunks, chat history, resumes, evaluations, and career roadmaps without leaving orphaned records in the database.
2. **Dual-Layer Enforcement**: Both the SQLAlchemy ORM session lifecycle and the underlying relational database enforce referential integrity.
3. **Preservation of Conversational Context**: If an uploaded reference document is deleted, associated chat sessions are not destroyed; instead, `ChatSession.document_id` is safely set to `NULL`, preserving conversational history while reflecting the document's removal.
4. **SQLite Parity with Production RDBMS**: Explicitly enabling foreign key enforcement via SQLite PRAGMA guarantees that development behavior matches production PostgreSQL constraints identically.

---

## ADR-09: Generative AI Provider Abstraction via BaseAIProvider and Factory

### Context
Higher-level application services (RAG retrieval, Resume Analyzer, Study Assistant, Career Roadmap) require generative LLM capabilities. Binding business logic directly to a proprietary SDK (e.g. `openai` or `google.genai`) risks vendor lock-in, testing complexity, fragile credential handling, and deployment rigidity.

### Decision
Establish a provider-neutral abstract contract (`BaseAIProvider`) in `backend/app/providers/base.py` defining standardized `generate(prompt, system_prompt=None, temperature=None, max_tokens=None)` semantics returning structured `ProviderResponse` and `UsageMetadata` objects. Concrete implementations (`DemoProvider`, `OpenAICompatibleProvider`, `GeminiProvider`) are instantiated exclusively via a centralized provider factory (`get_provider()`), with lazy client initialization and automated secret sanitization (`sanitize_sensitive_data`).

### Rationale
1. **Decoupled Architecture**: High-level domain services depend exclusively on the generic `BaseAIProvider` protocol, enabling seamless LLM swapping without code modifications.
2. **Multi-Model Support**: Supports commercial OpenAI models, self-hosted open-source inference servers (Ollama, vLLM, Groq) via `OPENAI_BASE_URL`, and Google Gemini multimodal models.
3. **Defensive Security**: API keys are backend-only environment variables; exceptions and logs pass through regex-based credential masking to guarantee zero secret leakage.
4. **Resilient Failure Modes**: Translates diverse third-party exceptions into controlled, typed application errors (`ProviderAuthenticationError`, `ProviderTimeoutError`, `ProviderRequestError`, `ProviderResponseError`).

---

## ADR-10: Deterministic Zero-Credential Demo Provider Engine

### Context
Automated CI/CD pipelines, local developer environments, and evaluator test runs often operate without paid API keys or active internet connections. Unhandled missing credentials causing startup crashes create immediate onboarding friction.

### Decision
Implement `DemoProvider` as the first-class default provider (`AI_PROVIDER=demo`). The engine runs entirely locally on CPU, makes zero network socket connections, requires no API keys, and deterministically synthesizes structured domain responses for 5 core interaction archetypes:
1. Executive Summaries (`summary`)
2. Document-Grounded Q&A (`document_grounded`, with explicit separation of citations and synthesis, and safe rejection of missing context)
3. Multiple Choice Questions (`mcq`)
4. Career Roadmaps and Learning Milestones (`career`)
5. General Conceptual Explanations (`explanation`)

### Rationale
1. **Zero-Friction Evaluation**: Anyone can clone and run the application instantly without external cloud accounts.
2. **Deterministic Test Verification**: Tests run identically and predictably without flaky network timeouts or non-deterministic token sampling.
3. **Honest Grounding**: When no reference context is supplied for document-grounded queries, the demo provider explicitly warns that no context exists rather than hallucinating answers.

---

## ADR-11: Study Assistant & Document-Grounded Chat Architecture

### Context
Users require conversational study assistance combining multi-turn interactive dialogues with document-grounded question answering and general technical mentoring.

### Decision
Implement chat orchestration in a dedicated service layer (`backend/app/services/chat_service.py`), leveraging existing domain models (`ChatSession`, `ChatMessage`), existing RAG retrieval (`retrieve_chunks`), and existing AI provider abstractions (`get_provider()`).

### Rationale
1. **Separation of Concerns**: Chat session state, message persistence, and bounded history management are decoupled from low-level RAG vector arithmetic and raw LLM clients.
2. **Context Branching**: Automatically branches between document-grounded RAG (when `session.document_id` exists) and general study mentoring (when `document_id` is `None`), eliminating unnecessary vector lookups.
3. **Threshold-Gated Cost Savings**: If document retrieval falls below `RAG_SIMILARITY_THRESHOLD`, the service terminates early with an honest insufficient-evidence response without incurring LLM token costs or risking hallucinations.
4. **Bounded Conversation History**: Sliding-window history truncation capped at 10 messages and 6,000 characters guarantees whole-message preservation while defending against context overflow.
5. **Zero-Key Deterministic Demo Mode**: Fully compatible with `DemoProvider` for reproducible offline evaluation and automated testing.

---

## ADR-12: Deterministic Resume Analyzer & Skill Normalization Architecture

### Context
Evaluating candidate resumes against modern industry job descriptions requires structured profile extraction (education, work experience, projects, technical skills), alias-resilient skill taxonomy mapping, and gap analysis scoring. Relying on unconstrained generative LLMs for ATS match scores introduces non-deterministic scoring variations, hallucinated competencies, high token costs, and opaque ranking biases.

### Decision
Implement a two-stage deterministic Resume Analyzer:
1. **Deterministic Information Extraction & Taxonomy Normalization**:
   - Resumes are validated, sanitized, stored under `uploads/resumes/`, and parsed page-by-page using PyMuPDF (`fitz`) or multi-encoding fallback sequence (`clean_text`).
   - Section headers (`EDUCATION`, `EXPERIENCE`, `SKILLS`, `PROJECTS`, `CERTIFICATIONS`) are detected with boundary-safe regular expressions.
   - Skills are matched using boundary lookarounds (`(?<![a-zA-Z0-9])` and `(?![a-zA-Z0-9])`) against a curated taxonomy dictionary (`SKILL_ALIAS_MAP`) normalizing aliases to canonical terms (`k8s` -> `Kubernetes`, `py` -> `Python`, `reactjs` -> `React`, `ts` -> `TypeScript`, `postgres` -> `PostgreSQL`).
2. **Transparent & Auditable ATS Scoring**:
   $$\text{match\_score} = \left( \frac{|\text{Matched Required Skills}|}{|\text{Total Required Skills in Job Description}|} \right) \times 100$$
   - Edge case safe: If no Job Description is provided, `match_score` is `None` with full extracted skills returned. If Job Description has 0 technical skills, `match_score` is `100.0`.
   - Traceable recommendations are synthesized directly from missing technical competencies and structural sections.
3. **Idempotent Persistence & Multi-Tenant Security**:
   - Resumes are bound to `user_id` (`X-User-Id` header).
   - Analysis records upsert idempotently on re-analysis against new job descriptions without violating foreign key or uniqueness constraints.
   - Deleting a resume cascades to delete all linked analyses and the physical file on disk.

### Rationale
1. **Deterministic & Explainable**: Candidates and recruiters receive consistent, auditable match scores and direct explanations of missing competencies without black-box drift.
2. **Zero-Token Cost & Offline Capability**: Runs 100% locally on CPU without requiring external API keys or cloud services.
3. **High Throughput**: Extraction and scoring execute in `< 50ms` per document.
4. **Security & Privacy**: Resumes are protected by strict per-user ownership boundaries.
