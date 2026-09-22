# SahayakAI — React + Vite Frontend

Enterprise-grade, modern, and responsive web interface for **SahayakAI (सहायक AI)** — the Unified AI-Powered Student Learning & Career Platform.

---

## 🚀 Features & Modules

1. **Dashboard (`/`)**
   - High-level metric cards: Processed study materials, active chat sessions, uploaded resumes, and active career roadmaps.
   - Quick launch buttons to upload documents, start AI chat sessions, and view 12-week roadmap milestones.
   - Live system status badge communicating with `/api/health`.

2. **Study Documents (`/documents` & `/documents/:id`)**
   - Drag-and-drop file upload for PDF and TXT documents (up to 10MB).
   - Title customization and immediate vector embedding generation toggle (`auto_embed=true`).
   - Detailed document inspection view: file metadata, word/page counts, extracted keyword tags.
   - Vector chunk inspector with chunk index, page attribution, vector status badge, character count, and copy button.
   - Direct document-grounded Q&A testing console with adjustable `top_k` and `similarity_threshold`.

3. **Study Assistant (`/chat`)**
   - Multi-turn conversational interface with session management.
   - Document-grounded chat sessions with automatic cosine similarity vector retrieval.
   - Collapsible citations drawer showing chunk references, page numbers, similarity match percentages, and excerpts.
   - Insufficient evidence badge when document context lacks verification.
   - Quick starter prompt suggestions.

4. **Resume Analyzer & ATS Scorecard (`/resumes`)**
   - Resume file upload for PDF and TXT formats.
   - Target job description textarea with one-click ATS match evaluation.
   - Visual ATS Score gauge (0–100%) with dynamic color-coding (Strong, Moderate, Needs Improvement).
   - Extracted resume skills breakdown.
   - Matched vs. Missing skills comparison cards.
   - Actionable recommendations list to maximize recruiter visibility.

5. **Career Profile (`/career/profile`)**
   - Profile management form for academic degree, experience level, and target role from 10 curated disciplines (Software Engineer, Data Scientist, Machine Learning Engineer, Cloud Solutions Architect, DevOps Engineer, Cybersecurity Analyst, Full Stack Developer, Product Manager, AI Research Scientist, Data Engineer) or custom disciplines.
   - Interactive skill and interest tag selectors.

6. **Career Roadmap (`/career/roadmap`)**
   - Synthesizes user profile and optional resume skill gaps into a structured 12-week progression.
   - 6 bi-weekly milestones (Weeks 1–2, 3–4, 5–6, 7–8, 9–10, 11–12) with objectives, target competencies, and hands-on project deliverables.
   - Recommended capstone portfolio projects with difficulty and descriptions.
   - Core technical interview topics and question categories.

---

## 🛠️ Tech Stack

- **Framework**: React 18 with TypeScript
- **Build Tool**: Vite 6
- **Routing**: React Router DOM v6
- **Styling**: Tailwind CSS 3 with PostCSS and Autoprefixer
- **Icons**: Lucide React
- **Testing**: Vitest & React Testing Library with JSDOM
- **HTTP Client**: Fetch API with centralized `X-User-Id` header injection and structured error envelope parsing

---

## 🏃 Getting Started

### Prerequisites
- Node.js (v18+)
- Backend running on `http://localhost:8000` (FastAPI)

### Installation
```bash
cd frontend
npm install
```

### Environment Configuration
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Default contents:
```env
VITE_API_BASE_URL=http://localhost:8000/api
```

### Development Server
```bash
npm run dev
```
The application will be accessible at `http://localhost:5173`.

### Running Tests
```bash
npm test
```

### Production Build
```bash
npm run build
```
Build output is generated in `dist/`.

---

## 🔒 Security & Guardrails

- **Zero Secret Exposure**: Provider API keys (`OPENAI_API_KEY`, `GEMINI_API_KEY`) remain strictly on the backend. The frontend consumes the unified `/api` gateway.
- **Pre-Auth User Scoping**: Requests attach `X-User-Id` header (configurable via the top navbar Dev User selector) enforcing cross-user database isolation.
- **Defensive Error Handling**: Non-2xx API responses are parsed into typed `ApiError` instances displaying user-friendly error banners and toast messages.
