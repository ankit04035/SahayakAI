# SahayakAI — Frontend Architecture & Contract Integration

## 1. Overview
The SahayakAI frontend is a modern Single Page Application (SPA) designed to serve as the user-facing interface for university students and career aspirants. It is built strictly against the frozen API contract defined in `docs/frontend_contract.md` and integrated with the FastAPI backend foundation.

---

## 2. Directory Structure

```
frontend/
├── index.html                 # Single page application host
├── package.json               # Dependencies and build scripts
├── vite.config.ts             # Vite bundler and Vitest test runner configuration
├── tailwind.config.js         # Tailwind typography, theme, and color tokens
├── tsconfig.json              # TypeScript compilation configuration
├── src/
│   ├── api/                   # HTTP client and modular API endpoints
│   │   ├── client.ts          # Central fetch client with X-User-Id and error envelope parsing
│   │   ├── health.ts          # /api/health endpoint
│   │   ├── documents.ts       # /api/documents upload, inspection, chunks, embed, ask
│   │   ├── chat.ts            # /api/chat sessions and messaging
│   │   ├── resumes.ts         # /api/resumes upload and ATS analysis
│   │   └── career.ts          # /api/career profile and 12-week roadmap generation
│   ├── components/
│   │   └── common/            # Reusable UI component library
│   │       ├── Alert.tsx
│   │       ├── Badge.tsx
│   │       ├── Button.tsx
│   │       ├── Card.tsx
│   │       ├── EmptyState.tsx
│   │       ├── LoadingSpinner.tsx
│   │       ├── Modal.tsx
│   │       └── Skeleton.tsx
│   ├── context/
│   │   └── UserContext.tsx    # Global Dev User ID state and localStorage persistence
│   ├── layouts/
│   │   └── MainLayout.tsx     # App shell with responsive sidebar, live health badge, user switch
│   ├── pages/                 # Full feature views
│   │   ├── DashboardPage.tsx
│   │   ├── DocumentsPage.tsx
│   │   ├── DocumentDetailPage.tsx
│   │   ├── ChatPage.tsx
│   │   ├── ResumePage.tsx
│   │   ├── CareerProfilePage.tsx
│   │   ├── CareerRoadmapPage.tsx
│   │   └── NotFoundPage.tsx
│   ├── styles/
│   │   └── index.css          # Tailwind base directives and custom scrollbar utilities
│   ├── test/                  # Test suites
│   │   ├── setup.ts           # Vitest environment setup and mocks
│   │   ├── formatters.test.ts # Utility unit tests
│   │   ├── apiClient.test.ts  # API client headers, error parsing, and URL resolution tests
│   │   ├── flows.test.tsx     # Component view flows (Docs, Chat, Resume, Career, Dashboard)
│   │   └── App.test.tsx       # Routing and component integration tests
│   ├── types/                 # Frozen TypeScript interfaces
│   │   ├── api.ts
│   │   ├── document.ts
│   │   ├── chat.ts
│   │   ├── resume.ts
│   │   └── career.ts
│   ├── utils/
│   │   ├── formatters.ts      # Byte, date, percent, and string truncation helpers
│   │   └── errors.ts          # Error mapping and extraction
│   ├── App.tsx                # Client-side router declarations
│   └── main.tsx               # Root React entry point
```

---

## 3. Communication & Contract Adherence

### 3.1 Base URL & Environment
All API calls route through `VITE_API_BASE_URL` (configured via `frontend/.env`, default: `http://localhost:8000/api`). The API client normalizes input URLs to ensure trailing slashes and the `/api` prefix are consistently structured.

### 3.2 Pre-Auth Scoping (`X-User-Id`)
To support development and testing prior to auth integration, the user selector in the header toggles between Dev User IDs (e.g., User 1, 2, 3, 42). The `UserContext` persists this to `localStorage` (`sahayakai_user_id`) and automatically attaches `X-User-Id` to all outgoing API requests.

Cross-user isolation is strictly enforced on the backend: User A cannot read, modify, or delete resources belonging to User B.

### 3.3 CORS Configuration
The backend allows origins defined in `CORS_ORIGINS`:
- `http://localhost:5173`
- `http://127.0.0.1:5173`
Both hostnames are supported for local Vite browser development.

### 3.4 Error Envelope Handling
When the backend returns an error:
```json
{
  "status": "error",
  "error_code": "DOCUMENT_NOT_FOUND",
  "message": "Document with id 999 does not exist.",
  "details": null
}
```
The `apiRequest` wrapper parses this envelope and throws an `ApiError` with status code, error code, and message for UI alerts.

---

## 4. End-to-End User Flow Verification (STEP 13)

The complete end-to-end integration flow has been verified via `scripts/verify_step13.py` and live browser testing across all 5 major workflows:

1. **Workflow A: Study Documents & RAG Grounded Q&A**
   - Upload synthetic PDF/TXT document.
   - Inspect document metadata and keywords.
   - Inspect vector chunk partition list with token counts.
   - Query grounded question: returns answer with chunk sources, page attribution, and similarity scores.
   - Query unrelated question: triggers `insufficient_evidence=True` UI alert banner.
   - Delete document: cascades to vector chunks and index.

2. **Workflow B: Study Assistant Multi-Turn Chat**
   - General academic chat without document binding.
   - Multi-turn conversation preserves message history in prompt.
   - Document-grounded chat session with citations drawer.
   - Insufficient evidence fallback.

3. **Workflow C: Resume Analyzer & ATS Scorecard**
   - Synthetic candidate resume upload.
   - Structured skill extraction.
   - ATS match evaluation against target job description.
   - Dynamic ATS score gauge, matched skills, missing skills, and actionable recommendations.
   - Analysis history persistence.

4. **Workflow D: Career Profile & User Scoping**
   - Create profile with degree, skills, experience, and target role from 10 curated disciplines.
   - Verify persistence across page reloads.
   - User 2 cannot access User 1 profile (`HTTP 404`).
   - Update competencies and verify instant update.

5. **Workflow E: 12-Week Career Roadmap**
   - Synthesizes user profile and optional resume skill gaps.
   - Generates 6 bi-weekly milestones (Weeks 1–2, 3–4, 5–6, 7–8, 9–10, 11–12).
   - Structured capstone projects and technical interview topics.
   - Cascading deletion and cleanup.

6. **Workflow F: Dashboard Integration**
   - Live backend metric counters for documents, chat sessions, resumes, and roadmap state.

---

## 5. Verification Baseline
- **Vitest Suite**: 19 unit & integration tests passing (100% green across 4 test suites).
- **Production Build**: `npm run build` completed with 0 errors in ~4 seconds.
- **Backend Regression**: All 236 pytest regression tests verified passing.
- **Integration Script**: `scripts/verify_step13.py` executed 9 verification steps successfully.
- **Security Audit**: 0 hardcoded secrets or API keys in frontend source or production bundles.
- **Mirror Parity**: 100% SHA-256 match between root `frontend/` and `SahayakAI/frontend/`.
