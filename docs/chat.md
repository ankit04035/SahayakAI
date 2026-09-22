# SahayakAI — Study Assistant & Document-Grounded Chat Architecture

**Status:** COMPLETE (Step 8 Verified)  
**Modules:** `backend/app/services/chat_service.py`, `backend/app/routes/chat.py`, `backend/app/services/chat_prompt.py`  
**Default Provider:** DemoProvider (Deterministic, Zero-API-key)  

---

## 1. System Overview

The SahayakAI Study Assistant provides conversational academic mentoring and document-grounded question answering. It allows students and learners to:
1. Conduct multi-turn interactive study dialogues.
2. Ask questions grounded in uploaded textbooks, lecture notes, or technical papers.
3. Receive factual explanations with source page and chunk citations.
4. Pose general computer science and academic queries without document attachments.

```mermaid
graph TD
    Client[Client / Frontend] -->|POST /api/chat/sessions/{id}/messages| Router[Chat Router: routes/chat.py]
    Router --> Service[Chat Service: services/chat_service.py]

    subgraph 1. Validation & Persistence
        Service --> ValMsg[Validate Message Bounds & Non-whitespace]
        Service --> ValSession[Verify Session Exists & User Ownership]
        Service --> SaveUserMsg[(Persist User ChatMessage)]
    end

    subgraph 2. History & Retrieval Branching
        SaveUserMsg --> HistWindow[Sliding Window: Bounded History 10 Turns / 6000 Chars]
        HistWindow --> CheckDoc{Has document_id?}
        CheckDoc -- Yes --> RAGRetrieve[Step 7 RAG Retrieval Engine]
        RAGRetrieve --> CheckEv{Similarity >= 0.35?}
        CheckEv -- No --> InsufficientEv[Return Insufficient Evidence & Skip LLM]
        CheckEv -- Yes --> FormatContext[Bounded Context Builder]
        CheckDoc -- No --> GenStudy[General Study Mentor Branch]
    end

    subgraph 3. Prompting & AI Synthesis
        FormatContext --> GroundedPrompt[Grounded Prompt + Injection Defense]
        GenStudy --> PedagogicalPrompt[Pedagogical Mentoring Prompt]
        GroundedPrompt --> Provider[get_provider: Demo / OpenAI / Gemini]
        PedagogicalPrompt --> Provider
        Provider --> AnswerText[Synthesized Response]
    end

    subgraph 4. Persistence & Output
        InsufficientEv --> SaveAssistMsg[(Persist Assistant ChatMessage)]
        AnswerText --> SaveAssistMsg
        SaveAssistMsg --> ReturnResp[Structured ChatResponse with Citations]
    end
```

---

## 2. Session & Message Lifecycles

### Session Lifecycle
- **Creation (`POST /api/chat/sessions`):**
  - Requires valid `user_id` (defaults to active dev user if omitted).
  - Optionally associates with `document_id`. If specified, verifies that the document belongs to the requesting user (`DocumentOwnershipError` on mismatch).
  - Enforces session title bounds (`CHAT_MAX_TITLE_CHARS=255`, defaults to `"New Chat"`).
- **Listing (`GET /api/chat/sessions`):** Returns all sessions owned by the user, optionally filtered by `document_id`.
- **Detail (`GET /api/chat/sessions/{session_id}`):** Enforces ownership (`ChatAccessDeniedError` / HTTP 403 on mismatch).
- **Deletion (`DELETE /api/chat/sessions/{session_id}`):** Cascades deletion to all contained `ChatMessage` records.
- **Document Deletion Safety:** Deleting an uploaded document sets `session.document_id = NULL` via foreign key `ondelete="SET NULL"`. The session remains intact and seamlessly transitions into a general study session.

### Message Lifecycle
1. User sends a message via `POST /api/chat/sessions/{session_id}/messages`.
2. Service validates that message is non-empty, non-whitespace, and within `CHAT_MAX_MESSAGE_CHARS` (default 4,000 characters).
3. The user message is persisted immediately to SQLite with `role="user"`.
4. The service generates an answer (grounded or general study).
5. The assistant message is persisted to SQLite with `role="assistant"` and citation metadata in `source_metadata`.
6. Full `ChatResponse` is returned to client.

---

## 3. Grounded vs. General Study Chat Flows

### Document-Grounded Chat Flow
- Triggered when `session.document_id is not None`.
- Calls `retrieve_chunks(document_id, query, top_k, similarity_threshold)` from Step 7 RAG engine.
- If no chunks meet `RAG_SIMILARITY_THRESHOLD` (0.35):
  - Bypasses LLM provider invocation.
  - Returns `insufficient_evidence=True`, `grounded=False`, `sources=[]`.
  - Assistant message records: *"The provided document does not contain sufficient relevant information to answer this question."*
- If qualifying evidence is found:
  - Context is assembled under character budget (`RAG_MAX_CONTEXT_CHARS=12000`).
  - System prompt enforces strict tutor grounding and untrusted source warnings (prompt injection defense).
  - Invokes AI provider, records citations in `source_metadata`, and returns `grounded=True`.

### General Study Chat Flow
- Triggered when `session.document_id is None`.
- Completely skips vector retrieval (zero database search overhead).
- System prompt establishes pedagogical mentor persona for structured technical explanations.
- Invokes AI provider (`DemoProvider` dispatches to `_handle_general_explanation`).
- Returns `grounded=False`, `insufficient_evidence=False`, `sources=[]`.

---

## 4. Conversation History Strategy

To support multi-turn dialogues without exceeding token limits or causing mid-sentence truncation:
- **Sliding Window:** Loads the most recent prior turns up to `CHAT_HISTORY_MAX_MESSAGES` (default `10`).
- **Character Budget Cap:** Bounded by `CHAT_MAX_HISTORY_CHARS` (default `6,000`).
- **Completeness Rule:** Traverses backwards from newest to oldest. If adding an entire turn would breach the budget, older turns are pruned as whole units. No turn is sliced in the middle of a sentence.
- **Prompt Presentation:** Chronological order is restored before prompt formatting:
  ```markdown
  Conversation History:
  User: What is dynamic programming?
  Assistant: Dynamic programming is an optimization technique...
  ```

---

## 5. Security & Ownership Enforcement

- **User Session Isolation:** Users can only query, list, or message sessions where `session.user_id == requesting_user_id`. Cross-user attempts return `HTTP 403 Forbidden` (`SESSION_ACCESS_DENIED`).
- **Document Association Isolation:** Users cannot create a session attached to another user's document (`HTTP 403 Forbidden`, `DOCUMENT_ACCESS_DENIED`).
- **Prompt Injection Defense:** Context is wrapped in explicit untrusted source boundaries, with instructions forbidding the model from executing commands found in document text.
- **Secret Scrubbing:** All provider exceptions pass through `sanitize_sensitive_data()`, stripping API keys and tokens before error response serialization.
