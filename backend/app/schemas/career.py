"""
CareerProfile and Roadmap Pydantic Schemas.
Defines validation and serialization models for user profiles and learning roadmaps.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator
from backend.app.schemas.common import TimestampSchema


class SkillRecommendation(BaseModel):
    """Structured skill recommendation detail."""

    name: str = Field(..., max_length=100)
    status: str = Field(..., description="'missing', 'possessed', or 'recommended'")
    importance: str = Field(default="high", description="'high', 'medium', or 'supplementary'")


class ProjectRecommendation(BaseModel):
    """Structured portfolio project recommendation."""

    title: str = Field(..., max_length=255)
    skills: List[str] = Field(default_factory=list)
    description: str = Field(..., max_length=2000)
    difficulty: str = Field(default="Intermediate", max_length=50)


class WeeklyPlanItem(BaseModel):
    """Individual milestone in the multi-week learning plan."""

    week_range: str = Field(..., max_length=50, examples=["Week 1-2"])
    focus: str = Field(..., max_length=255)
    learning_goals: List[str] = Field(default_factory=list)
    deliverable: str = Field(..., max_length=500)


class InterviewTopicItem(BaseModel):
    """Technical interview preparation topic."""

    topic: str = Field(..., max_length=255)
    sample_questions: Optional[List[str]] = None


class CareerProfileBase(BaseModel):
    """Base career profile fields with defensive limits."""

    degree: Optional[str] = Field(None, max_length=255, description="Academic degree or qualification")
    current_skills: Optional[List[str]] = Field(default_factory=list, description="Self-reported or extracted skills")
    experience: Optional[str] = Field(None, max_length=10000, description="Summary of work experience or background")
    interests: Optional[List[str]] = Field(default_factory=list, description="Personal or professional technical interests")
    target_role: str = Field(..., min_length=2, max_length=255, description="Desired professional role")

    @field_validator("target_role")
    @classmethod
    def validate_target_role(cls, v: str) -> str:
        cleaned = v.strip()
        if len(cleaned) < 2:
            raise ValueError("Target role must be at least 2 characters long.")
        return cleaned

    @field_validator("current_skills", "interests")
    @classmethod
    def validate_list_bounds(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        if v is not None:
            if len(v) > 50:
                raise ValueError("Skill/interest lists cannot exceed 50 items.")
            cleaned = [item.strip() for item in v if item and item.strip() and len(item.strip()) <= 100]
            return cleaned
        return []


class CareerProfileCreate(CareerProfileBase):
    """Payload for creating a career profile."""

    user_id: Optional[int] = Field(None, description="Optional user ID; defaults to authenticated dev user")


class CareerProfileUpdate(BaseModel):
    """Payload for updating an existing career profile."""

    degree: Optional[str] = Field(None, max_length=255)
    current_skills: Optional[List[str]] = None
    experience: Optional[str] = Field(None, max_length=10000)
    interests: Optional[List[str]] = None
    target_role: Optional[str] = Field(None, min_length=2, max_length=255)

    @field_validator("target_role")
    @classmethod
    def validate_optional_target_role(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            cleaned = v.strip()
            if len(cleaned) < 2:
                raise ValueError("Target role must be at least 2 characters long.")
            return cleaned
        return None

    @field_validator("current_skills", "interests")
    @classmethod
    def validate_optional_list_bounds(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        if v is not None:
            if len(v) > 50:
                raise ValueError("Skill/interest lists cannot exceed 50 items.")
            return [item.strip() for item in v if item and item.strip() and len(item.strip()) <= 100]
        return None


class CareerProfileRead(CareerProfileBase, TimestampSchema):
    """Public career profile response schema."""

    id: int
    user_id: int

    model_config = ConfigDict(from_attributes=True)


class RoadmapGenerateRequest(BaseModel):
    """Request payload to generate a personalized career roadmap."""

    target_role: Optional[str] = Field(None, min_length=2, max_length=255, description="Optional override for target role")
    resume_id: Optional[int] = Field(None, description="Optional Resume ID to incorporate extracted skills from Step 9")
    custom_interests: Optional[List[str]] = Field(None, description="Optional additional focus areas")


class RoadmapBase(BaseModel):
    """Base roadmap fields."""

    title: str = Field(..., min_length=1, max_length=255)
    recommended_skills: Optional[List[str]] = None
    missing_skills: Optional[List[str]] = None
    projects: Optional[List[Dict[str, Any]]] = None
    learning_order: Optional[List[str]] = None
    weekly_plan: Optional[List[Dict[str, Any]]] = None
    interview_topics: Optional[List[str]] = None
    recommendation_reasons: Optional[List[str]] = None


class RoadmapCreate(RoadmapBase):
    """Payload for persisting a generated career roadmap."""

    career_profile_id: int


class RoadmapRead(RoadmapBase, TimestampSchema):
    """Public roadmap response schema."""

    id: int
    career_profile_id: int

    model_config = ConfigDict(from_attributes=True)
