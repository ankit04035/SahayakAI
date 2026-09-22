# Resume Analyzer & ATS Scorecard Specification

## 1. Overview
The **Resume Analyzer** is a core functional module of the SahayakAI platform (Step 9). It ingests candidate resumes in PDF or plain text formats, extracts structured biographical, educational, and professional competencies using deterministic NLP pipelines, and evaluates candidates against job descriptions using an explainable, transparent ATS match scoring formula.

Unlike opaque AI scoring systems, SahayakAI implements an auditable, deterministic scoring engine that provides candidates with traceable skill gap analyses and actionable recommendations.

```
                      +-----------------------------+
                      |   Candidate Resume Upload   |
                      |        (PDF or TXT)         |
                      +--------------+--------------+
                                     |
                                     v
                      +-----------------------------+
                      | File Validation & Security  |
                      |  (MIME, Size, Sanitization) |
                      +--------------+--------------+
                                     |
                                     v
                      +-----------------------------+
                      |   Deterministic Extraction  |
                      |   (PyMuPDF / UTF-8 Decoder) |
                      +--------------+--------------+
                                     |
                                     v
                      +-----------------------------+
                      |   Text Cleaning & Sections  |
                      |     (regex boundary parser) |
                      +--------------+--------------+
                                     |
                                     v
                      +-----------------------------+
                      | Skill Extraction & Taxonomy |
                      |    (Canonical Alias Map)    |
                      +--------------+--------------+
                                     |
           +-------------------------+-------------------------+
           | (With Optional Job Description)                   | (Without Job Description)
           v                                                   v
+-----------------------------+                 +-----------------------------+
|    Skill Gap Evaluation     |                 |  Profile Inventory Synthesis|
|  - Matched: A ∩ B           |                 |  - Extracted skills list    |
|  - Missing: B \ A           |                 |  - Education credentials    |
|  - Score: (|Matched| / |B|) |                 |  - Experience records       |
+--------------+--------------+                 |  - Structural feedback      |
               |                                +-----------------------------+
               v
+-----------------------------+
| Traceable Recommendations   |
| & Persistence (SQLite / DB) |
+-----------------------------+
```

---

## 2. Document Processing & Structured Extraction

### 2.1 File Ingestion & Storage Isolation
- Resumes are validated against accepted extensions (`.pdf`, `.txt`) and mime types (`application/pdf`, `text/plain`).
- Files are size-limited via `MAX_UPLOAD_SIZE_BYTES` (default 10 MB).
- Filenames are sanitized using `sanitize_filename` (removing path traversal tokens like `../`, `..\`) and stored with a cryptographically unique UUID prefix under `uploads/resumes/`.

### 2.2 Extraction Engine
- **PDF Extraction**: Extracted page-by-page using PyMuPDF (`fitz`), preserving text blocks while stripping non-printable characters.
- **TXT Extraction**: Multi-encoding fallback sequence (`utf-8`, `utf-8-sig`, `latin-1`, `cp1252`).
- **Text Normalization**: Reuses the core NLP `clean_text` pipeline from Step 5 to standardize whitespace, quotes, and punctuation.

### 2.3 Section & Entity Parsing
- Identifies functional headers: `EDUCATION`, `EXPERIENCE`, `SKILLS`, `PROJECTS`, `CERTIFICATIONS`.
- **Education Extraction**: Captures degree credentials (B.Tech, B.S., M.S., Ph.D., MBA, etc.), institutions, and graduation years.
- **Experience Extraction**: Identifies engineering roles, titles, company affiliations, and duration patterns.
- **Graceful Fallback**: In the absence of standard headings, the extractor parses freeform body text without throwing parsing errors.

---

## 3. Skill Taxonomy & Canonical Normalization

Skill extraction uses a comprehensive, deterministic dictionary mapping aliases and synonyms to canonical names without hallucinations:

### 3.1 Taxonomy Examples
| User Variant / Alias | Canonical Skill |
| :--- | :--- |
| `k8s` | `Kubernetes` |
| `py`, `python3` | `Python` |
| `reactjs`, `react.js` | `React` |
| `nodejs`, `node.js` | `Node.js` |
| `postgres`, `postgresql` | `PostgreSQL` |
| `golang` | `Go` |
| `ts` | `TypeScript` |
| `cpp`, `c++` | `C++` |
| `csharp`, `c#` | `C#` |
| `ci/cd`, `cicd` | `CI/CD` |
| `amazon web services` | `AWS` |
| `gcp`, `google cloud` | `GCP` |

### 3.2 False-Positive Mitigation & Boundary Safety
- Skills are matched using boundary lookarounds (`(?<![a-zA-Z0-9])` and `(?![a-zA-Z0-9])`).
- Short names (such as "Go") use capitalization sensitivity (`Go`) or term pairing (`golang`, `go programming`) to prevent false positive matches against everyday English verbs ("we go", "going", "category").
- C++ and C# employ specialized regexes accounting for symbol characters (`+` and `#`).

---

## 4. ATS Match Scoring Formula

The match score is strictly deterministic, transparent, and auditable:

$$\text{match\_score} = \left( \frac{|\text{Matched Required Skills}|}{|\text{Total Required Skills in Job Description}|} \right) \times 100$$

### Edge Cases:
1. **No Job Description Provided**:
   - `match_score`: `None`
   - `matched_skills`: `[]`
   - `missing_skills`: `[]`
2. **Job Description with 0 Identifiable Technical Skills**:
   - `match_score`: `100.0` (all 0 requirements satisfied)
   - `matched_skills`: `[]`
   - `missing_skills`: `[]`
3. **No Overlapping Skills**:
   - `match_score`: `0.0`
   - `matched_skills`: `[]`
   - `missing_skills`: List of all required skills in the job description.

---

## 5. Recommendation Engine

The recommendation engine generates actionable, constructive advice:
1. **Target Competencies**: Identifies the highest priority missing technical competencies required by the target role.
2. **Structural Completeness**: Flags missing sections (e.g., absence of explicit education degrees or experience entries).
3. **Impact Maximization**: Encourages quantifiable metrics (e.g., "% latency reduction", "user scale", "dollar savings").

---

## 6. Multi-Tenant User Isolation & Security

- Every `Resume` is strictly associated with a `user_id`.
- Pre-auth development uses header `X-User-Id` or query/form parameter `user_id`.
- Cross-user operations return HTTP 403 Forbidden with `RESUME_ACCESS_DENIED`.
- Cascade deletion ensures deleting a `Resume` purges the physical file on disk and cascades to delete all linked `ResumeAnalysis` records.

---

## 7. API Endpoints

### 7.1 Upload Resume
- **POST** `/api/resumes`
- **Content-Type**: `multipart/form-data`
- **Body**: `file` (PDF/TXT), optional `user_id`
- **Headers**: Optional `X-User-Id`
- **Status**: 201 Created

### 7.2 List Resumes
- **GET** `/api/resumes`
- **Status**: 200 OK

### 7.3 Get Resume Metadata
- **GET** `/api/resumes/{resume_id}`
- **Status**: 200 OK (or 403 / 404)

### 7.4 Analyze Resume
- **POST** `/api/resumes/{resume_id}/analyze`
- **Body** (optional): `{"job_description": "Seeking Python, FastAPI, Docker..."}`
- **Status**: 200 OK (or 403 / 404)

### 7.5 List Analyses
- **GET** `/api/resumes/{resume_id}/analyses`
- **Status**: 200 OK

### 7.6 Delete Resume
- **DELETE** `/api/resumes/{resume_id}`
- **Status**: 200 OK
