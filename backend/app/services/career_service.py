"""
Career Profile and Roadmap Generation Service.
Implements career profile management, deterministic skill gap analysis,
role taxonomy alignment, milestone-based learning plan synthesis,
and AI-assisted pedagogical recommendations.
"""

import logging
from typing import Any, Dict, List, Optional, Set, Tuple
from sqlalchemy.orm import Session

from backend.app.models.career import CareerProfile, Roadmap
from backend.app.models.resume import Resume, ResumeAnalysis
from backend.app.models.user import User
from backend.app.nlp.role_taxonomy import get_role_taxonomy
from backend.app.nlp.skill_extractor import normalize_skill
from backend.app.providers.factory import get_provider
from backend.app.schemas.career import (
    CareerProfileCreate,
    CareerProfileUpdate,
    RoadmapGenerateRequest,
)
from backend.app.services.career_exceptions import (
    CareerProfileAccessDeniedError,
    CareerProfileNotFoundError,
    InvalidCareerProfileError,
    RoadmapAccessDeniedError,
    RoadmapGenerationError,
    RoadmapNotFoundError,
)
from backend.app.services.document_service import get_or_create_default_user

logger = logging.getLogger("sahayakai.career_service")


# ==============================================================================
# PROFILE MANAGEMENT
# ==============================================================================

def get_career_profile(db: Session, user_id: Optional[int] = None) -> CareerProfile:
    """
    Retrieve the career profile for the specified user.
    """
    if user_id is None:
        user = get_or_create_default_user(db)
        resolved_user_id = user.id
    else:
        resolved_user_id = user_id

    profile = db.query(CareerProfile).filter(CareerProfile.user_id == resolved_user_id).first()
    if not profile:
        raise CareerProfileNotFoundError(message=f"Career profile not found for user {resolved_user_id}")
    return profile


def upsert_career_profile(
    db: Session,
    profile_in: CareerProfileCreate,
    user_id: Optional[int] = None,
) -> CareerProfile:
    """
    Idempotently create or update a user's CareerProfile.
    """
    if user_id is None:
        user = get_or_create_default_user(db)
        resolved_user_id = user.id
    else:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            user = get_or_create_default_user(db)
            resolved_user_id = user.id
        else:
            resolved_user_id = user_id

    # Normalize input skills
    normalized_skills = []
    if profile_in.current_skills:
        normalized_skills = sorted(list({normalize_skill(s) for s in profile_in.current_skills if s and s.strip()}))

    existing_profile = db.query(CareerProfile).filter(CareerProfile.user_id == resolved_user_id).first()

    if existing_profile:
        existing_profile.degree = profile_in.degree
        existing_profile.current_skills = normalized_skills
        existing_profile.experience = profile_in.experience
        existing_profile.interests = profile_in.interests or []
        existing_profile.target_role = profile_in.target_role
        profile = existing_profile
        logger.info("Updated career profile for user %d (target_role: '%s')", resolved_user_id, profile.target_role)
    else:
        profile = CareerProfile(
            user_id=resolved_user_id,
            degree=profile_in.degree,
            current_skills=normalized_skills,
            experience=profile_in.experience,
            interests=profile_in.interests or [],
            target_role=profile_in.target_role,
        )
        db.add(profile)
        logger.info("Created new career profile for user %d (target_role: '%s')", resolved_user_id, profile.target_role)

    db.commit()
    db.refresh(profile)
    return profile


def update_career_profile(
    db: Session,
    profile_in: CareerProfileUpdate,
    user_id: Optional[int] = None,
) -> CareerProfile:
    """
    Update fields on an existing career profile.
    """
    profile = get_career_profile(db=db, user_id=user_id)

    if profile_in.degree is not None:
        profile.degree = profile_in.degree
    if profile_in.current_skills is not None:
        profile.current_skills = sorted(list({normalize_skill(s) for s in profile_in.current_skills if s and s.strip()}))
    if profile_in.experience is not None:
        profile.experience = profile_in.experience
    if profile_in.interests is not None:
        profile.interests = profile_in.interests
    if profile_in.target_role is not None:
        profile.target_role = profile_in.target_role

    db.commit()
    db.refresh(profile)
    logger.info("Patched career profile ID=%d for user %d", profile.id, profile.user_id)
    return profile


def delete_career_profile(db: Session, user_id: Optional[int] = None) -> bool:
    """
    Delete a career profile and cascade deletion to its roadmaps.
    """
    profile = get_career_profile(db=db, user_id=user_id)
    db.delete(profile)
    db.commit()
    logger.info("Deleted career profile ID=%d for user %d", profile.id, profile.user_id)
    return True


# ==============================================================================
# SKILL GAP & ROADMAP SYNTHESIS ENGINE
# ==============================================================================

def compute_skill_gaps(
    current_skills: List[str],
    target_role: str,
) -> Dict[str, Any]:
    """
    Deterministically compare normalized current skills against target role taxonomy.

    Returns:
        dict containing taxonomy metadata, possessed skills, missing skills, and recommended skills.
    """
    taxonomy = get_role_taxonomy(target_role)
    norm_current: Set[str] = {normalize_skill(s) for s in current_skills if s and s.strip()}

    required_set: Set[str] = set(taxonomy["required_skills"])
    recommended_set: Set[str] = set(taxonomy["recommended_skills"])

    already_possessed = sorted(list(norm_current & required_set))
    missing_skills = sorted(list(required_set - norm_current))

    # Recommended skills: supplementary skills from taxonomy not possessed + missing required skills
    supplementary_missing = sorted(list(recommended_set - norm_current))
    all_recommended = sorted(list(set(missing_skills + supplementary_missing)))

    return {
        "canonical_role": taxonomy["role"],
        "required_skills": taxonomy["required_skills"],
        "already_possessed": already_possessed,
        "missing_skills": missing_skills,
        "recommended_skills": all_recommended,
        "learning_stages": taxonomy["learning_stages"],
        "default_projects": taxonomy["default_projects"],
        "interview_topics": taxonomy["interview_topics"],
    }


def construct_learning_order(
    missing_skills: List[str],
    recommended_skills: List[str],
    stages: List[Dict[str, Any]],
) -> List[str]:
    """
    Construct a pedagogical order of skills to learn based on stage sequencing.
    """
    order: List[str] = []
    seen: Set[str] = set()

    # Priority 1: Missing skills matching stages in order
    for stage in stages:
        for sk in stage.get("skills", []):
            if sk in missing_skills and sk not in seen:
                order.append(sk)
                seen.add(sk)

    # Priority 2: Any remaining missing skills
    for sk in missing_skills:
        if sk not in seen:
            order.append(sk)
            seen.add(sk)

    # Priority 3: Supplementary recommended skills
    for sk in recommended_skills:
        if sk not in seen:
            order.append(sk)
            seen.add(sk)

    return order


def build_weekly_plan(
    target_role: str,
    missing_skills: List[str],
    stages: List[Dict[str, Any]],
    projects: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Construct a structured 12-week progression plan.
    """
    p1_title = projects[0]["title"] if projects else "Core Practical Project"
    p2_title = projects[1]["title"] if len(projects) > 1 else "Capstone Production System"

    top_missing = missing_skills[:4] if missing_skills else ["Advanced System Architecture"]

    return [
        {
            "week_range": "Week 1-2",
            "focus": f"Foundation & Core Languages for {target_role}",
            "learning_goals": [
                f"Master core syntax and patterns in {top_missing[0] if top_missing else 'primary language'}",
                "Configure modern development environment and Git version control",
                "Write clean, modular code with automated unit testing",
            ],
            "deliverable": "Working repository demonstrating modular code structure and test coverage (>80%).",
        },
        {
            "week_range": "Week 3-4",
            "focus": "Data Architecture, APIs & Frameworks",
            "learning_goals": [
                f"Study framework best practices ({top_missing[1] if len(top_missing) > 1 else 'RESTful APIs'})",
                "Design relational schemas, indices, and database transaction boundaries",
                "Implement structured error handling and input validation",
            ],
            "deliverable": "Interactive API service communicating with a persisted database.",
        },
        {
            "week_range": "Week 5-6",
            "focus": f"Portfolio Project Development: {p1_title}",
            "learning_goals": [
                f"Implement core business logic for {p1_title}",
                "Integrate asynchronous operations, caching, and database pooling",
                "Write integration tests verifying edge cases",
            ],
            "deliverable": f"Completed MVP of {p1_title} with comprehensive test suite.",
        },
        {
            "week_range": "Week 7-8",
            "focus": "Cloud Deployment, Containers & Tooling",
            "learning_goals": [
                f"Containerize applications using multi-stage Docker builds",
                f"Study supplementary tools ({top_missing[2] if len(top_missing) > 2 else 'CI/CD pipelines'})",
                "Implement automated linting, security scanning, and container orchestration",
            ],
            "deliverable": "Containerized service deploying automatically through a CI/CD pipeline.",
        },
        {
            "week_range": "Week 9-10",
            "focus": f"Advanced Capstone: {p2_title}",
            "learning_goals": [
                f"Architect and build {p2_title} focusing on high reliability",
                "Implement distributed caching, rate limiting, and observability",
                "Document architecture with architecture diagrams and API specs",
            ],
            "deliverable": f"Production-grade {p2_title} deployed with live documentation and metrics.",
        },
        {
            "week_range": "Week 11-12",
            "focus": "System Design, Interview Preparation & Review",
            "learning_goals": [
                "Review high-yield technical interview topics for target role",
                "Practice architectural trade-offs: latency, consistency, fault tolerance",
                "Complete mock coding interviews and polish GitHub portfolio",
            ],
            "deliverable": "Interview-ready portfolio with documented case studies and resume alignment.",
        },
    ]


def synthesize_recommendation_reasons(
    target_role: str,
    already_possessed: List[str],
    missing_skills: List[str],
    degree: Optional[str],
    interests: Optional[List[str]],
    ai_explanation: Optional[str] = None,
) -> List[str]:
    """
    Generate traceable rationale explaining why each recommendation was formed.
    """
    reasons: List[str] = []

    # 1. Target Role Requirement Alignment
    if missing_skills:
        reasons.append(
            f"Role Alignment: The target role '{target_role}' requires foundational mastery in {', '.join(missing_skills[:4])}, which are currently missing from your active profile."
        )

    # 2. Existing Competency Leverage
    if already_possessed:
        reasons.append(
            f"Strength Leverage: You already possess verified competencies in {', '.join(already_possessed[:4])}, allowing you to bypass introductory topics and accelerate directly into applied system design."
        )
    else:
        reasons.append(
            f"Foundational Ramp-Up: As you are beginning your journey towards '{target_role}', the roadmap starts with essential language and data modeling fundamentals."
        )

    # 3. Academic Background Context
    if degree:
        reasons.append(
            f"Academic Context: Recommendations are structured to complement your academic background ({degree}) by emphasizing hands-on production engineering over abstract theory."
        )

    # 4. Personal Interests
    if interests:
        reasons.append(
            f"Interest Synergy: Your expressed interest in {', '.join(interests[:3])} is woven into the advanced capstone project phase."
        )

    # 5. AI Reasoning Enrichment
    if ai_explanation and len(ai_explanation.strip()) > 30:
        for line in ai_explanation.strip().splitlines():
            line_clean = line.strip().lstrip("#-*• ")
            if len(line_clean) > 25:
                reasons.append(f"AI Career Advisory: {line_clean}")
                break

    return reasons


def generate_roadmap(
    db: Session,
    request: Optional[RoadmapGenerateRequest] = None,
    user_id: Optional[int] = None,
) -> Roadmap:
    """
    Generate a personalized, transparent, and reproducible Career Roadmap.
    Integrates CareerProfile, optional ResumeAnalysis, and AI provider abstraction.
    """
    profile = get_career_profile(db=db, user_id=user_id)

    # Determine effective target role
    effective_role = (request.target_role.strip() if request and request.target_role and request.target_role.strip() else profile.target_role)
    if not effective_role:
        raise InvalidCareerProfileError("Career profile must have a valid target role.")

    # Determine candidate skills (Profile skills + optional Resume skills)
    combined_skills = list(profile.current_skills or [])

    # Check for resume integration
    resume_id = request.resume_id if request else None
    if resume_id is not None:
        # Enforce user ownership of the resume
        resume = db.query(Resume).filter(Resume.id == resume_id).first()
        if not resume:
            raise RoadmapGenerationError(f"Resume ID {resume_id} not found.")
        if resume.user_id != profile.user_id:
            raise CareerProfileAccessDeniedError(f"Access denied: resume {resume_id} does not belong to user {profile.user_id}")

        analysis = db.query(ResumeAnalysis).filter(ResumeAnalysis.resume_id == resume.id).first()
        if analysis and analysis.extracted_skills:
            if isinstance(analysis.extracted_skills, list):
                combined_skills.extend(analysis.extracted_skills)
            elif isinstance(analysis.extracted_skills, dict):
                for skill_list in analysis.extracted_skills.values():
                    if isinstance(skill_list, list):
                        combined_skills.extend(skill_list)

    # Add custom interests if passed
    effective_interests = list(profile.interests or [])
    if request and request.custom_interests:
        effective_interests.extend(request.custom_interests)

    # Compute deterministic skill gaps
    gap_result = compute_skill_gaps(current_skills=combined_skills, target_role=effective_role)

    canonical_role = gap_result["canonical_role"]
    already_possessed = gap_result["already_possessed"]
    missing_skills = gap_result["missing_skills"]
    recommended_skills = gap_result["recommended_skills"]
    stages = gap_result["learning_stages"]
    projects = gap_result["default_projects"]
    interview_topics = gap_result["interview_topics"]

    # Pedagogical order of learning
    learning_order = construct_learning_order(missing_skills, recommended_skills, stages)

    # Weekly plan
    weekly_plan = build_weekly_plan(canonical_role, missing_skills, stages, projects)

    # AI Provider Enrichment (Optional reasoning)
    ai_explanation = None
    try:
        provider = get_provider()
        ai_prompt = (
            f"Provide career roadmap reasoning for a candidate pursuing {canonical_role}. "
            f"Current verified skills: {', '.join(already_possessed) if already_possessed else 'None'}. "
            f"Identified skill gaps: {', '.join(missing_skills) if missing_skills else 'None'}."
        )
        ai_resp = provider.generate(prompt=ai_prompt, system_prompt="You are an expert technical career mentor.")
        ai_explanation = ai_resp.generated_text
    except Exception as err:
        logger.warning("AI Provider explanation generation skipped or failed: %s", err)

    # Synthesize recommendation reasons
    recommendation_reasons = synthesize_recommendation_reasons(
        target_role=canonical_role,
        already_possessed=already_possessed,
        missing_skills=missing_skills,
        degree=profile.degree,
        interests=effective_interests,
        ai_explanation=ai_explanation,
    )

    # Persist Roadmap record
    title = f"{canonical_role} Mastery Roadmap"
    roadmap = Roadmap(
        career_profile_id=profile.id,
        title=title,
        recommended_skills=recommended_skills,
        missing_skills=missing_skills,
        projects=projects,
        learning_order=learning_order,
        weekly_plan=weekly_plan,
        interview_topics=interview_topics,
        recommendation_reasons=recommendation_reasons,
    )
    db.add(roadmap)
    db.commit()
    db.refresh(roadmap)

    logger.info("Generated and persisted roadmap ID=%d for profile ID=%d (%s)", roadmap.id, profile.id, title)
    return roadmap


def list_roadmaps(db: Session, user_id: Optional[int] = None) -> List[Roadmap]:
    """
    List all roadmaps belonging to the requesting user's career profile.
    """
    try:
        profile = get_career_profile(db=db, user_id=user_id)
    except CareerProfileNotFoundError:
        return []
    return db.query(Roadmap).filter(Roadmap.career_profile_id == profile.id).order_by(Roadmap.id.desc()).all()


def get_roadmap(db: Session, roadmap_id: int, user_id: Optional[int] = None) -> Roadmap:
    """
    Retrieve a specific roadmap with ownership enforcement.
    """
    roadmap = db.query(Roadmap).filter(Roadmap.id == roadmap_id).first()
    if not roadmap:
        raise RoadmapNotFoundError(roadmap_id=roadmap_id)

    if user_id is not None:
        if roadmap.career_profile is None or roadmap.career_profile.user_id != user_id:
            logger.warning("Access denied: user %d attempted to access roadmap %d", user_id, roadmap.id)
            raise RoadmapAccessDeniedError(roadmap_id=roadmap_id)

    return roadmap


def delete_roadmap(db: Session, roadmap_id: int, user_id: Optional[int] = None) -> bool:
    """
    Delete a specific roadmap with ownership check.
    """
    roadmap = get_roadmap(db=db, roadmap_id=roadmap_id, user_id=user_id)
    db.delete(roadmap)
    db.commit()
    logger.info("Deleted roadmap ID=%d", roadmap_id)
    return True
