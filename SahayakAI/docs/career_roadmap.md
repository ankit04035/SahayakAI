# Career Profile & Personalized Career Roadmap Specification

## 1. Overview
The **Career Profile & Personalized Career Roadmap** module (Step 10) provides learners, job-seekers, and working professionals with structured career goal management and reproducible, milestone-based learning plans.

By synthesizing a candidate's self-reported competencies, academic credentials, work history, target role, and optional **Resume Analyzer** (Step 9) extracted skills, the module deterministically identifies skill gaps against a curated industry taxonomy and generates actionable, 12-week learning roadmaps.

```
                      +-----------------------------+
                      |        CareerProfile        |
                      |  (Degree, Skills, Role, Exp)|
                      +--------------+--------------+
                                     |
                                     v
                      +-----------------------------+
                      |   Optional Resume Analysis  |
                      |     (Step 9 Extracted)      |
                      +--------------+--------------+
                                     |
                                     v
                      +-----------------------------+
                      | Canonical Skill Normalizer  |
                      |    (Alias Map Resolution)   |
                      +--------------+--------------+
                                     |
                                     v
                      +-----------------------------+
                      | Curated Role Taxonomy Match |
                      |   (10 Core Software Roles)  |
                      +--------------+--------------+
                                     |
                                     v
                      +-----------------------------+
                      | Deterministic Gap Analysis  |
                      | - Possessed: C ∩ Required   |
                      | - Missing: Required \ C     |
                      | - Recommended: Missing ∪ Rec|
                      +--------------+--------------+
                                     |
                                     v
                      +-----------------------------+
                      | Pedagogical Staged Order &  |
                      | 12-Week Milestone Synthesis |
                      +--------------+--------------+
                                     |
                                     v
                      +-----------------------------+
                      |  AI Provider Enrichment     |
                      |  (Contextual Career Advice) |
                      +--------------+--------------+
                                     |
                                     v
                      +-----------------------------+
                      | Persisted Roadmap & SQLite  |
                      |  (Structured JSON Schema)   |
                      +-----------------------------+
```

---

## 2. Curated Role Taxonomy

To guarantee reproducibility and prevent black-box recommendation drift, SahayakAI relies on an isolated, curated role taxonomy (`backend/app/nlp/role_taxonomy.py`) covering 10 industry roles:

1. **Python Developer**
2. **Backend Developer**
3. **Frontend Developer**
4. **Full Stack Developer**
5. **Data Analyst**
6. **Data Scientist**
7. **Machine Learning Engineer**
8. **AI/ML Engineer**
9. **DevOps Engineer**
10. **Cloud Engineer**

*Note: This is an initial curated industry baseline, not an exhaustive labor-market database. It is designed to be easily extensible without altering service logic.*

### Role Taxonomy Structure
For each role, the taxonomy defines:
- **`required_skills`**: Core technical competencies mandatory for production readiness.
- **`recommended_skills`**: High-value supplementary electives strengthening candidate depth.
- **`learning_stages`**: Sequential pedagogical progression (Phase 1 Foundations, Phase 2 Applied APIs/Tools, Phase 3 Scaling/Cloud, Phase 4 System Design & Portfolio).
- **`default_projects`**: 2-3 structured portfolio project blueprints with target skills, description, and difficulty level.
- **`interview_topics`**: High-yield technical discussion points and architectural trade-offs.

---

## 3. Deterministic Skill Gap Logic

Given candidate competencies $C$ (normalized via `normalize_skill` and alias dictionary `SKILL_ALIAS_MAP`) and target role requirements $K_{	ext{req}}$ and $K_{	ext{rec}}$:

1. **Already Possessed Skills**:
   $$\text{Possessed} = C \cap K_{\text{req}}$$
2. **Missing Skills**:
   $$\text{Missing} = K_{\text{req}} \setminus C$$
3. **Recommended Skills**:
   $$\text{Recommended} = (K_{\text{rec}} \setminus C) \cup \text{Missing}$$

The roadmap clearly distinguishes between:
- **Possessed Skills**: Verified proficiencies allowing the learner to accelerate directly into advanced modules.
- **Missing Skills**: Core requirements needed to reach minimal professional qualification for the role.
- **Supplementary Recommended Skills**: Strategic skills that elevate the candidate above standard entry-level benchmarks.

---

## 4. 12-Week Progression Structure

The roadmap partitions the skill gaps into 6 structured bi-weekly milestones:
- **Weeks 1–2: Foundation & Core Language Mastery** (Primary missing programming languages, Git, and clean modular code).
- **Weeks 3–4: Data Architecture, APIs & Frameworks** (Framework best practices, relational schema design, transactional integrity).
- **Weeks 5–6: Portfolio Project 1 Development** (Hands-on development of the first major domain project).
- **Weeks 7–8: Cloud Deployment, Containers & Tooling** (Docker containerization, automated CI/CD pipelines, and cloud hosting).
- **Weeks 9–10: Advanced Capstone Project Development** (High-reliability distributed system, caching, rate limiting, and observability).
- **Weeks 11–12: System Design, Interview Preparation & Polish** (High-yield interview trade-offs, mock assessments, and resume alignment).

---

## 5. Resume Integration

Users can optionally pass `resume_id` during roadmap generation.
The service:
1. Validates that the requested `Resume` belongs to the requesting user (`403 Forbidden` if unauthorized).
2. Retrieves the corresponding `ResumeAnalysis` generated in Step 9.
3. Incorporates the extracted technical skills into the candidate's verified skill inventory, preventing redundant recommendations for skills already demonstrated on the resume.

---

## 6. Generative AI Provider Integration

The roadmap leverages the provider abstraction layer (`BaseAIProvider` via `get_provider()`):
- **Role of AI**: Synthesizes natural-language career advisory statements and contextual pedagogical rationale.
- **Guaranteed Fallback & Demo Mode**: In `AI_PROVIDER=demo` mode, uses the deterministic local rule engine (`_handle_career_request()`), generating structured, repeatable outputs with zero external API keys.
- **Defensive Design**: Core skill gaps, learning orders, and project recommendations remain deterministic and immune to LLM hallucination.

---

## 7. Multi-Tenant User Isolation & Security

- `CareerProfile` and `Roadmap` records are strictly bound to `user_id`.
- Pre-auth requests use `X-User-Id` header or `user_id` query/form parameter.
- Cross-user profile access or roadmap access returns `403 Forbidden`.
- Deleting a `CareerProfile` cascades to remove all associated `Roadmap` records.

---

## 8. REST API Reference

### 8.1 Profile Endpoints
- **POST** `/api/career/profile`: Upsert candidate career profile (201 Created).
- **GET** `/api/career/profile`: Retrieve user profile (200 OK, 404 Not Found).
- **PUT** `/api/career/profile`: Update specific profile fields (200 OK).
- **DELETE** `/api/career/profile`: Delete profile and cascade to roadmaps (200 OK).

### 8.2 Roadmap Endpoints
- **POST** `/api/career/roadmaps/generate`: Generate and persist career roadmap (201 Created).
- **GET** `/api/career/roadmaps`: List user roadmaps (200 OK).
- **GET** `/api/career/roadmaps/{roadmap_id}`: Retrieve specific roadmap by ID (200 OK, 403, 404).
- **DELETE** `/api/career/roadmaps/{roadmap_id}`: Delete specific roadmap by ID (200 OK, 403, 404).
