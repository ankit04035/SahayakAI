# SahayakAI — Retrieval-Augmented Generation (RAG) Architecture & Implementation

**Status:** COMPLETE (Step 7 Verified)  
**Embedding Model:** sentence-transformers/all-MiniLM-L6-v2 (384 dimensions)  
**Default Provider:** DemoProvider (Deterministic, Zero-API-key)  

---

## 1. System Architecture

SahayakAI implements a local, privacy-first Retrieval-Augmented Generation (RAG) pipeline designed to run on consumer hardware without leaking confidential study documents or user notes to external vector databases.

```mermaid
graph TD
    subgraph 1. Ingestion & Preprocessing
        Doc[Uploaded PDF / TXT] --> Chunker[Sliding Window Text Chunker]
        Chunker --> DBChunks[(SQLite DocumentChunk Records)]
    end

    subgraph 2. Embedding Layer
        DBChunks --> ModelMgr[EmbeddingModelManager]
        ModelMgr --> MiniLM[all-MiniLM-L6-v2 Engine]
        MiniLM --> L2Norm[Unit L2 Normalization]
        L2Norm --> JSONStore[DocumentChunk.embedding JSON Array]
    end

    subgraph 3. Retrieval Engine
        QueryText[User Question] --> QueryNorm[Query Preprocessing]
        QueryNorm --> QueryEmbed[384-dim Query Vector]
        JSONStore --> CandidateLoad[Scoped Document Chunks]
        CandidateLoad --> DotSim[Cosine Similarity Computation]
        QueryEmbed --> DotSim
        DotSim --> RankSort[Deterministic Sort: (-sim, chunk_index)]
        RankSort --> ThreshFilter{Sim >= Threshold (0.35)?}
        ThreshFilter -- No --> NoEv[Insufficient Evidence Bypass]
        ThreshFilter -- Yes --> TopK[Top-K Candidates]
    end

    subgraph 4. Context & Generation
        TopK --> Dedupe[Deduplication & Hash Check]
        Dedupe --> BudgetCap[Max Context Budget 12000 Chars]
        BudgetCap --> Reorder[Reading Order Re-sort: chunk_index]
        Reorder --> PromptGen[Prompt Builder with Injection Defense]
        PromptGen --> LLMProvider[BaseAIProvider / DemoProvider]
        LLMProvider --> AnswerOut[Grounded Response with Citations]
    end
```

---

## 2. Mathematical Similarity Formulation

Cosine similarity measures the angular alignment between query vector $\mathbf{q}$ and chunk vector $\mathbf{c}$:

$$\text{cosine}(\mathbf{q}, \mathbf{c}) = \frac{\mathbf{q} \cdot \mathbf{c}}{\|\mathbf{q}\|_2 \|\mathbf{c}\|_2}$$

Because all vectors produced by our embedding pipeline (`all-MiniLM-L6-v2`) are unit $L_2$-normalized during generation ($\|\mathbf{q}\|_2 = 1.0$ and $\|\mathbf{c}\|_2 = 1.0$), the denominator evaluates to $1.0$:

$$\text{cosine}(\mathbf{q}, \mathbf{c}) = \mathbf{q} \cdot \mathbf{c} = \sum_{i=1}^{384} q_i \cdot c_i$$

### Numerical Safeguards
1. **Dimension Validation**: Both vectors must strictly possess 384 finite float elements.
2. **Zero-Vector Handling**: Degenerate zero-magnitude vectors safely return a similarity score of `0.0` instead of causing division by zero.
3. **Clamping**: Due to floating-point imprecision (e.g. `1.00000002`), dot products are explicitly clamped to the closed interval `[-1.0, 1.0]`.

---

## 3. Retrieval Algorithm & Tie-Breaking

The retrieval pipeline (`backend/app/rag/retrieval.py`) implements deterministic candidate selection:

1. **Document Scoping**: Chunks are strictly filtered by `document_id`. Cross-document chunk leakage is impossible.
2. **Deserialization & Validation**: JSON-encoded float vectors are loaded and checked for corruption (NaN, infinity, non-numeric values).
3. **Deterministic Ranking**: If two chunks share identical similarity scores, they are deterministically broken using their sequential `chunk_index`:
   $$\text{sort\_key} = (-\text{similarity\_score}, \text{chunk\_index})$$
4. **Similarity Threshold Filtering**: Chunks below `RAG_SIMILARITY_THRESHOLD` (default `0.35`) are dropped.
5. **Top-K Window**: The top $K$ scoring chunks (`RAG_TOP_K`, default `5`) are selected for context assembly.

---

## 4. Context Builder & Budget Protection

Selected chunks are processed by `backend/app/rag/context_builder.py`:

- **Duplicate Control**: Chunks with identical chunk IDs or SHA-256 text content hashes are discarded.
- **Budget Protection**: Characters are accumulated under `RAG_MAX_CONTEXT_CHARS` (default `12,000`). Once the budget is exhausted, candidate inclusion halts gracefully.
- **Reading Order Preservation**: While chunks are ranked by similarity for selection, they are re-sorted by ascending `chunk_index` before presentation to ensure natural narrative continuity.
- **Attribution Blocks**: Each chunk is formatted with markdown citation metadata:
  ```markdown
  --- Context Chunk 2 (Page 1) ---
  [Extracted chunk content...]
  ```

---

## 5. Prompt Construction & Injection Defense

The prompt builder (`backend/app/rag/prompt_builder.py`) wraps retrieved context in defensible instruction wrappers:

- **Untrusted Content Warning**: Instructs the LLM that context text is untrusted source data and must never be interpreted as system instructions, system prompts, or command overrides.
- **Insufficient Evidence Standard**: Instructs the LLM to decline to speculate if the question cannot be answered directly from the provided excerpts.
- **Delimiter Isolation**: System prompt and user context use distinct markdown delimiters (`Context:` and `Question:`) that match the `DemoProvider` parser.

---

## 6. Deterministic Demo Mode & Zero-API-Key Operation

When `AI_PROVIDER=demo`:
1. If no chunks exceed `RAG_SIMILARITY_THRESHOLD`, the service returns `insufficient_evidence=True` and `grounded=False` without calling the LLM.
2. If evidence is present, `DemoProvider` inspects the prompt's `Context:` block, extracts sentences matching keywords in the query, and formats a grounded, cited response with zero network latency and complete offline determinism.

---

## 7. Vector Database Roadmap

| Stage | Technology | Use Case |
| :--- | :--- | :--- |
| **Current (Step 7)** | SQLite JSON + NumPy Dot Product | Single-user local desktop, zero external services, complete privacy |
| **Near-Term** | `sqlite-vec` extension | Native C-level vector indexing directly inside SQLite database |
| **Production Multi-Tenant** | Qdrant / ChromaDB / pgvector | High-concurrency enterprise deployments with millions of chunks |
