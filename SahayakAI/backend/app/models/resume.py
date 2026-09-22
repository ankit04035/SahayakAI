"""
Resume and ResumeAnalysis Model Definitions.
Represents candidate resumes and structured analytical scorecards.
"""

from sqlalchemy import Column, Integer, String, Text, ForeignKey, JSON, Float
from sqlalchemy.orm import relationship
from backend.app.database import Base
from backend.app.models.base import TimestampMixin


class Resume(Base, TimestampMixin):
    """Uploaded candidate resume document."""

    __tablename__ = "resumes"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    original_filename = Column(String(255), nullable=False)
    stored_filename = Column(String(255), nullable=False)
    file_type = Column(String(50), nullable=False)
    file_size = Column(Integer, nullable=False)
    processing_status = Column(String(50), nullable=False, default="uploaded")

    # Relationships
    user = relationship("User", back_populates="resumes")
    analysis = relationship(
        "ResumeAnalysis",
        back_populates="resume",
        cascade="all, delete-orphan",
        passive_deletes=True,
        uselist=False,
    )

    def __repr__(self) -> str:
        return f"<Resume(id={self.id}, user_id={self.user_id}, filename='{self.original_filename}', status='{self.processing_status}')>"


class ResumeAnalysis(Base, TimestampMixin):
    """Structured assessment, skill breakdown, and ATS scoring output for a resume."""

    __tablename__ = "resume_analyses"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    resume_id = Column(
        Integer,
        ForeignKey("resumes.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    job_description = Column(Text, nullable=True)
    extracted_skills = Column(JSON, nullable=True)     # List[str] or Dict[str, List[str]]
    education_data = Column(JSON, nullable=True)       # List[Dict[str, Any]]
    experience_data = Column(JSON, nullable=True)      # List[Dict[str, Any]]
    matched_skills = Column(JSON, nullable=True)       # List[str]
    missing_skills = Column(JSON, nullable=True)       # List[str]
    match_score = Column(Float, nullable=True)         # 0.0 - 100.0 transparent ATS score
    recommendations = Column(JSON, nullable=True)      # List[str]

    # Relationships
    resume = relationship("Resume", back_populates="analysis")

    def __repr__(self) -> str:
        return f"<ResumeAnalysis(id={self.id}, resume_id={self.resume_id}, match_score={self.match_score})>"
