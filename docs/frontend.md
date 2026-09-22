# SahayakAI — Frontend Architecture & Contract Integration

## 1. Overview
The SahayakAI frontend is a modern Single Page Application (SPA) designed to serve as the user-facing interface for university students and career aspirants. It is built strictly against the frozen API contract defined in `docs/frontend_contract.md`.

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
All API calls route through `VITE_API_BASE_URL` (defaults to `http://localhost:8000/api`).

### 3.2 Pre-Auth Scoping (`X-User-Id`)
To support development and testing prior to auth integration, the user selector in the header toggles between Dev User IDs (e.g., 1, 2, 3, 42). The `UserContext` persists this to `localStorage` and automatically attaches `X-User-Id` to all API requests.

### 3.3 Error Envelope Handling
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

## 4. Verification Baseline
- **Vitest Suite**: 5 unit/integration tests passing.
- **Production Build**: `npm run build` completed with 0 errors.
- **Backend Parity**: All 236 pytest regression tests verified passing.
- **Mirror Parity**: 100% SHA-256 match between root `frontend/` and `SahayakAI/frontend/`.
