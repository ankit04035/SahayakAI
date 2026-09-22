"""
Resume and ResumeAnalysis Pydantic Schemas.
Defines validation and serialization models for resumes and evaluation metrics.
"""

from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, ConfigDict, Field
from backend.app.schemas.common import TimestampSchema


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
