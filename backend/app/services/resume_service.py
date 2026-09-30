"""
Resume Processing and Analysis Service.
Handles resume upload, text extraction using existing PyMuPDF infrastructure,
structured profile parsing, job description skill matching,
match score calculation, and recommendation synthesis.
"""

import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import fitz  # PyMuPDF
from sqlalchemy.orm import Session

from backend.app.config import get_settings
from backend.app.exceptions import AppException
from backend.app.models.resume import Resume, ResumeAnalysis
from backend.app.models.user import User
from backend.app.nlp.resume_parser import parse_structured_resume
from backend.app.nlp.skill_extractor import extract_skills
from backend.app.nlp.text_cleaner import clean_text
from backend.app.services.document_service import get_or_create_default_user
from backend.app.services.resume_exceptions import (
    ResumeAccessDeniedError,
    ResumeAnalysisAccessDeniedError,
    ResumeAnalysisNotFoundError,
    ResumeNotFoundError,
    ResumeProcessingError,
)
from backend.app.utils.file_validation import validate_file_content, validate_file_metadata
from backend.app.utils.filename import (
    generate_stored_filename,
    get_safe_storage_path,
    sanitize_filename,
)

logger = logging.getLogger("sahayakai.resume_service")


def create_resume_upload(
    file_content: bytes,
    original_filename: str,
    db: Session,
    user_id: Optional[int] = None,
) -> Resume:
    """
    Process and persist a candidate resume upload (reusing Step 5 file validation).
    """
    settings = get_settings()

    # 1. Validation
    ext = validate_file_metadata(original_filename, len(file_content))
    mime_type, enc_or_type = validate_file_content(file_content, ext)

    # 2. Resolve User
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

    # 3. Safe Storage
    if os.environ.get("VERCEL") == "1":
        upload_dir = Path("/tmp") / "resumes"
    else:
        upload_dir = Path(settings.UPLOAD_DIR) / "resumes"
    upload_dir.mkdir(parents=True, exist_ok=True)

    safe_original_name = sanitize_filename(original_filename)
    stored_filename = generate_stored_filename(original_filename)
    storage_path = get_safe_storage_path(upload_dir, stored_filename)

    try:
        with open(storage_path, "wb") as f:
            f.write(file_content)
    except Exception as err:
        logger.error("Failed to write resume to disk: %s", err, exc_info=True)
        raise AppException(
            message=f"Failed to persist resume file: {str(err)}",
            status_code=500,
            error_code="STORAGE_WRITE_ERROR",
        )

    # 4. Create Resume Record
    resume = Resume(
        user_id=resolved_user_id,
        original_filename=safe_original_name,
        stored_filename=stored_filename,
        file_type=ext,
        file_size=len(file_content),
        processing_status="completed",
    )
    db.add(resume)
    db.commit()
    db.refresh(resume)
    logger.info("Resume uploaded successfully: ID=%d, filename='%s'", resume.id, safe_original_name)
    return resume


def get_resume(db: Session, resume_id: int, user_id: Optional[int] = None) -> Resume:
    """
    Retrieve resume with ownership validation.
    """
    resume = db.query(Resume).filter(Resume.id == resume_id).first()
    if not resume:
        raise ResumeNotFoundError(resume_id=resume_id)

    if user_id is not None and resume.user_id != user_id:
        logger.warning("Access denied: user %d attempted to access resume %d owned by %d", user_id, resume.id, resume.user_id)
        raise ResumeAccessDeniedError(resume_id=resume_id)

    return resume


def list_resumes(db: Session, user_id: Optional[int] = None) -> List[Resume]:
    """
    List resumes belonging to user.
    """
    if user_id is None:
        user = get_or_create_default_user(db)
        resolved_user_id = user.id
    else:
        resolved_user_id = user_id

    return db.query(Resume).filter(Resume.user_id == resolved_user_id).order_by(Resume.id.desc()).all()


def delete_resume(db: Session, resume_id: int, user_id: Optional[int] = None) -> bool:
    """
    Delete resume and associated disk file.
    """
    resume = get_resume(db=db, resume_id=resume_id, user_id=user_id)
    settings = get_settings()
    base_dir = Path("/tmp") if os.environ.get("VERCEL") == "1" else Path(settings.UPLOAD_DIR)
    storage_path = base_dir / "resumes" / resume.stored_filename

    if storage_path.exists():
        try:
            storage_path.unlink()
        except Exception as err:
            logger.warning("Failed to remove resume file %s: %s", storage_path, err)

    db.delete(resume)
    db.commit()
    logger.info("Deleted resume ID=%d", resume_id)
    return True


def extract_resume_text(resume: Resume) -> str:
    """
    Extract and clean raw text from persisted resume file (reusing PyMuPDF / text decoder).
    """
    settings = get_settings()
    base_dir = Path("/tmp") if os.environ.get("VERCEL") == "1" else Path(settings.UPLOAD_DIR)
    storage_path = base_dir / "resumes" / resume.stored_filename

    if not storage_path.exists():
        raise ResumeProcessingError(f"Resume file '{resume.stored_filename}' not found on storage disk.")

    raw_bytes = storage_path.read_bytes()

    if resume.file_type == ".pdf":
        try:
            with fitz.open(stream=raw_bytes, filetype="pdf") as doc:
                text_parts = [page.get_text("text") for page in doc]
                raw_text = "\n\n".join(text_parts)
        except Exception as err:
            raise ResumeProcessingError(f"Failed to extract text from PDF: {str(err)}")
    else:
        # Plain text
        encodings = ["utf-8", "utf-8-sig", "latin-1", "cp1252"]
        raw_text = None
        for enc in encodings:
            try:
                raw_text = raw_bytes.decode(enc)
                break
            except UnicodeDecodeError:
                continue
        if raw_text is None:
            raw_text = raw_bytes.decode("utf-8", errors="replace")

    cleaned = clean_text(raw_text)
    if not cleaned:
        raise ResumeProcessingError("Resume text is empty or could not be extracted.")
    return cleaned


def generate_recommendations(
    structured_data: Dict[str, Any],
    missing_skills: List[str],
    match_score: Optional[float],
) -> List[str]:
    """
    Synthesize actionable, traceable recommendations based on extracted resume data and missing competencies.
    """
    recommendations: List[str] = []

    # 1. Missing Technical Competencies
    if missing_skills:
        top_missing = missing_skills[:5]
        recommendations.append(
            f"Target Skill Development: Consider acquiring or highlighting hands-on project experience in: {', '.join(top_missing)}."
        )

    # 2. Education Section Assessment
    if not structured_data.get("education"):
        recommendations.append(
            "Education Section: Ensure your highest academic credentials, degree title, university, and graduation year are clearly formatted."
        )

    # 3. Experience Section Assessment
    if not structured_data.get("experience"):
        recommendations.append(
            "Experience Section: Add relevant professional experience, internships, or open-source software contributions."
        )

    # 4. Project Highlights
    if not structured_data.get("projects"):
        recommendations.append(
            "Portfolio Projects: Showcase 2-3 prominent engineering projects demonstrating practical application of your core technical skills."
        )

    # 5. Quantifiable Impact
    recommendations.append(
        "Quantifiable Achievements: Strengthen bullet points by quantifying accomplishments with measurable metrics (e.g., % latency reduction, user scale, efficiency gains)."
    )

    return recommendations


def analyze_resume(
    db: Session,
    resume_id: int,
    job_description: Optional[str] = None,
    user_id: Optional[int] = None,
) -> ResumeAnalysis:
    """
    Execute full structured resume analysis, job description matching,
    and transparent scoring.

    Formula:
        match_score = (matched_required_skills / total_required_skills) * 100
        If total_required_skills == 0: match_score = 100.0 (all 0 requirements satisfied)
        If job_description is None: match_score = None, matched_skills = [], missing_skills = []
    """
    resume = get_resume(db=db, resume_id=resume_id, user_id=user_id)

    # 1. Extract raw text
    resume_text = extract_resume_text(resume)

    # 2. Structured parsing
    structured_data = parse_structured_resume(resume_text)
    resume_skills_set = set(structured_data["skills"])

    matched_skills: List[str] = []
    missing_skills: List[str] = []
    match_score: Optional[float] = None

    # 3. Job Description Skill Matching
    if job_description and job_description.strip():
        jd_clean = job_description.strip()
        jd_skills_list = extract_skills(jd_clean)
        jd_skills_set = set(jd_skills_list)

        matched_skills_set = resume_skills_set & jd_skills_set
        missing_skills_set = jd_skills_set - resume_skills_set

        matched_skills = sorted(list(matched_skills_set))
        missing_skills = sorted(list(missing_skills_set))

        if len(jd_skills_set) > 0:
            match_score = round((len(matched_skills) / len(jd_skills_set)) * 100.0, 1)
        else:
            match_score = 100.0

    # 4. Generate recommendations
    recommendations = generate_recommendations(
        structured_data=structured_data,
        missing_skills=missing_skills,
        match_score=match_score,
    )

    # 5. Persist or Update ResumeAnalysis record
    existing_analysis = db.query(ResumeAnalysis).filter(ResumeAnalysis.resume_id == resume.id).first()

    if existing_analysis:
        existing_analysis.job_description = job_description.strip() if job_description else None
        existing_analysis.extracted_skills = structured_data["skills"]
        existing_analysis.education_data = structured_data["education"]
        existing_analysis.experience_data = structured_data["experience"]
        existing_analysis.matched_skills = matched_skills
        existing_analysis.missing_skills = missing_skills
        existing_analysis.match_score = match_score
        existing_analysis.recommendations = recommendations
        analysis = existing_analysis
    else:
        analysis = ResumeAnalysis(
            resume_id=resume.id,
            job_description=job_description.strip() if job_description else None,
            extracted_skills=structured_data["skills"],
            education_data=structured_data["education"],
            experience_data=structured_data["experience"],
            matched_skills=matched_skills,
            missing_skills=missing_skills,
            match_score=match_score,
            recommendations=recommendations,
        )
        db.add(analysis)

    db.commit()
    db.refresh(analysis)
    logger.info("Completed analysis for resume ID=%d, match_score=%s", resume.id, match_score)
    return analysis


def get_analyses(db: Session, resume_id: int, user_id: Optional[int] = None) -> List[ResumeAnalysis]:
    """
    Get all analyses for a resume.
    """
    resume = get_resume(db=db, resume_id=resume_id, user_id=user_id)
    analyses = db.query(ResumeAnalysis).filter(ResumeAnalysis.resume_id == resume.id).all()
    return analyses


def get_analysis(db: Session, resume_id: int, analysis_id: int, user_id: Optional[int] = None) -> ResumeAnalysis:
    """
    Get a specific analysis with ownership checks.
    """
    resume = get_resume(db=db, resume_id=resume_id, user_id=user_id)
    analysis = (
        db.query(ResumeAnalysis)
        .filter(ResumeAnalysis.id == analysis_id, ResumeAnalysis.resume_id == resume.id)
        .first()
    )
    if not analysis:
        raise ResumeAnalysisNotFoundError(analysis_id=analysis_id)
    return analysis
