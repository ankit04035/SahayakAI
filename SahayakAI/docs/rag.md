# SahayakAI — Retrieval-Augmented Generation (RAG) Architecture

**Status:** IN PROGRESS (Step 6 Complete: Sentence Embeddings)  
**Version:** 1.0.0  

---

## 1. RAG Subsystem Overview

SahayakAI employs a local, private RAG pipeline designed to run on consumer hardware without sending confidential user study materials or resumes to external vector databases.

```mermaid
graph TD
    subgraph Step 5: Document Ingestion [Step 5: Document Ingestion (Completed)]
        Doc[Uploaded PDF / TXT] --> Chunker[Sliding Window Chunker]
        Chunker --> DBChunks[DocumentChunk Text Records]
    end

    subgraph Step 6: Embedding Layer [Step 6: Embedding Layer (Completed)]
        DBChunks --> ModelMgr[EmbeddingModelManager]
        ModelMgr --> SentenceTransformer[all-MiniLM-L6-v2: 384-dim]
        SentenceTransformer --> Norm[L2 Normalization]
        Norm --> VectorStore[Persist JSON Vectors to DocumentChunk.embedding]
        
        UserQuery[User Query] --> QueryEmbed[embed_query: 384-dim]
    end

    subgraph Step 7: Retrieval & Synthesis [Step 7: Retrieval & Synthesis (Future)]
        QueryEmbed -.-> Similarity[NumPy Dot Product Cosine Similarity]
        VectorStore -.-> Similarity
        Similarity -.-> TopK[Top-K Semantic Chunks]
        TopK -.-> PromptBuilder[Contextual Prompt Builder]
        PromptBuilder -.-> Provider[BaseAIProvider Generation]
    end
```

---

## 2. Current Implementation Status (Step 6)

### ✅ Implemented (Step 6: Transformer & Embeddings)
- **Model Engine**: `sentence-transformers` running `all-MiniLM-L6-v2`.
- **Dimensionality**: Strictly validated 384-dimensional floating-point vectors.
- **Normalization**: Unit L2 normalization on all vectors ($\|\mathbf{v}\|_2 = 1.0$).
- **Lifecycle**: Lazy in-process model caching via thread-safe `EmbeddingModelManager`.
- **Batch Processing**: Configurable `EMBEDDING_BATCH_SIZE=32` with transactional rollbacks.
- **Multilingual Input**: Robust vector generation across English, Hindi (Devanagari), and Hinglish.
- **Persistence**: SQLite-compatible JSON numeric arrays in `DocumentChunk.embedding` (zero pickle).

### ⏳ Future Work (Step 7: Retrieval & RAG Synthesis)
The following components are **NOT** yet implemented and will be built in Step 7:
- Top-K similarity retrieval (`numpy.dot` cosine scoring across chunk vectors).
- Similarity threshold filtering and relevance score ranking.
- Context window selection and dynamic prompt formatting with source citations.
- RAG question-answering chat endpoints and LLM integration.
