"""
CareerProfile and Roadmap Model Definitions.
Represents user aspirations, current skill inventories, and AI-generated career milestones.
"""

from sqlalchemy import Column, Integer, String, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from backend.app.database import Base
from backend.app.models.base import TimestampMixin


class CareerProfile(Base, TimestampMixin):
    """User career profile capturing skills, education, and target career goals."""

    __tablename__ = "career_profiles"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    degree = Column(String(255), nullable=True)
    current_skills = Column(JSON, nullable=True)       # List[str]
    experience = Column(Text, nullable=True)
    interests = Column(JSON, nullable=True)            # List[str]
    target_role = Column(String(255), nullable=False)

    # Relationships
    user = relationship("User", back_populates="career_profiles")
    roadmaps = relationship(
        "Roadmap",
        back_populates="career_profile",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    def __repr__(self) -> str:
        return f"<CareerProfile(id={self.id}, user_id={self.user_id}, target_role='{self.target_role}')>"


class Roadmap(Base, TimestampMixin):
    """Structured, milestone-based learning and skill acquisition plan."""

    __tablename__ = "roadmaps"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    career_profile_id = Column(
        Integer,
        ForeignKey("career_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title = Column(String(255), nullable=False)
    recommended_skills = Column(JSON, nullable=True)     # List[str]
    missing_skills = Column(JSON, nullable=True)         # List[str]
    projects = Column(JSON, nullable=True)               # List[Dict[str, Any]]
    learning_order = Column(JSON, nullable=True)         # List[str]
    weekly_plan = Column(JSON, nullable=True)            # List[Dict[str, Any]]
    interview_topics = Column(JSON, nullable=True)       # List[str]
    recommendation_reasons = Column(JSON, nullable=True) # List[str]

    # Relationships
    career_profile = relationship("CareerProfile", back_populates="roadmaps")

    def __repr__(self) -> str:
        return f"<Roadmap(id={self.id}, career_profile_id={self.career_profile_id}, title='{self.title}')>"
