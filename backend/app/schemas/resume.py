"""
Resume and ResumeAnalysis Pydantic Schemas.
Defines validation and serialization models for candidate resumes,
structured profiles, skill matching, and ATS evaluations.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, ConfigDict, Field, field_validator
from backend.app.schemas.common import TimestampSchema


class ResumeEducation(BaseModel):
    """Structured educational entry."""

    degree: Optional[str] = Field(None, description="Degree or credential name")
    institution: Optional[str] = Field(None, description="University or college name")
    year: Optional[str] = Field(None, description="Graduation year or date range")
    description: Optional[str] = Field(None, description="Raw credential line")


class ResumeExperience(BaseModel):
    """Structured work experience entry."""

    role: Optional[str] = Field(None, description="Job title or role")
    company: Optional[str] = Field(None, description="Employer name")
    duration: Optional[str] = Field(None, description="Employment dates")
    description: Optional[str] = Field(None, description="Raw job description or title line")


class ResumeStructuredData(BaseModel):
    """Complete structured representation extracted from resume text."""

    skills: List[str] = Field(default_factory=list, description="Extracted canonical technical skills")
    education: List[ResumeEducation] = Field(default_factory=list, description="Extracted education credentials")
    experience: List[ResumeExperience] = Field(default_factory=list, description="Extracted employment records")
    projects: List[str] = Field(default_factory=list, description="Extracted project highlights")
    certifications: List[str] = Field(default_factory=list, description="Extracted certifications")


class JobDescriptionRequest(BaseModel):
    """Payload for analyzing a resume against an optional job description."""

    job_description: Optional[str] = Field(
        default=None,
        description="Optional job description text to evaluate resume match against.",
        examples=["Seeking a Python Developer with experience in FastAPI, Docker, and PostgreSQL."],
    )

    @field_validator("job_description")
    @classmethod
    def validate_jd(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            cleaned = v.strip()
            if not cleaned:
                return None
            if len(cleaned) < 10:
                raise ValueError("Job description must be at least 10 characters long.")
            if len(cleaned) > 20000:
                raise ValueError("Job description cannot exceed 20,000 characters.")
            return cleaned
        return None


class ResumeBase(BaseModel):
    """Base resume fields."""

    original_filename: str = Field(..., min_length=1, max_length=255)
    file_type: str = Field(..., max_length=50)
    file_size: int = Field(..., gt=0)


class ResumeCreate(ResumeBase):
    """Payload for registering a resume upload."""

    user_id: int
    stored_filename: str = Field(..., min_length=1, max_length=255)
    processing_status: str = Field(default="uploaded", max_length=50)


class ResumeUpdate(BaseModel):
    """Payload for updating resume status."""

    processing_status: Optional[str] = None


class ResumeRead(ResumeBase, TimestampSchema):
    """Public resume response schema."""

    id: int
    user_id: int
    stored_filename: str
    processing_status: str

    model_config = ConfigDict(from_attributes=True)


class ResumeAnalysisBase(BaseModel):
    """Base analysis result fields."""

    job_description: Optional[str] = None
    extracted_skills: Optional[Union[List[str], Dict[str, Any]]] = None
    education_data: Optional[List[Dict[str, Any]]] = None
    experience_data: Optional[List[Dict[str, Any]]] = None
    matched_skills: Optional[List[str]] = None
    missing_skills: Optional[List[str]] = None
    match_score: Optional[float] = Field(None, ge=0.0, le=100.0)
    recommendations: Optional[List[str]] = None


class ResumeAnalysisCreate(ResumeAnalysisBase):
    """Payload for persisting a completed resume analysis."""

    resume_id: int


class ResumeAnalysisRead(ResumeAnalysisBase, TimestampSchema):
    """Public analysis response schema."""

    id: int
    resume_id: int

    model_config = ConfigDict(from_attributes=True)
