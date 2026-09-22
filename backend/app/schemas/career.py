"""
CareerProfile and Roadmap Pydantic Schemas.
Defines validation and serialization models for user profiles and learning roadmaps.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field
from backend.app.schemas.common import TimestampSchema


class CareerProfileBase(BaseModel):
    """Base career profile fields."""

    degree: Optional[str] = Field(None, max_length=255)
    current_skills: Optional[List[str]] = None
    experience: Optional[str] = None
    interests: Optional[List[str]] = None
    target_role: str = Field(..., min_length=1, max_length=255)


class CareerProfileCreate(CareerProfileBase):
    """Payload for creating a career profile."""

    user_id: int


class CareerProfileUpdate(BaseModel):
    """Payload for updating a career profile."""

    degree: Optional[str] = None
    current_skills: Optional[List[str]] = None
    experience: Optional[str] = None
    interests: Optional[List[str]] = None
    target_role: Optional[str] = None


class CareerProfileRead(CareerProfileBase, TimestampSchema):
    """Public career profile response schema."""

    id: int
    user_id: int

    model_config = ConfigDict(from_attributes=True)


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
