"""Resume chunk model."""
import uuid
from datetime import datetime
from sqlalchemy import ForeignKey, Integer, Text, DateTime, JSON, String, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column
from pgvector.sqlalchemy import Vector
from app.db.base import Base
import enum


class SectionType(str, enum.Enum):
    """Enum for resume section types."""
    ABOUT_ME = "about_me"
    WORK_EXPERIENCE = "work_experience"
    EDUCATION = "education"
    CERTIFICATIONS = "certifications"
    ACHIEVEMENTS = "achievements"
    SKILLS = "skills"
    INTEREST = "interest"
    PERSONAL_PROFILE = "personal_profile"


class ResumeChunk(Base):
    """Resume chunk model for vector search."""
    
    __tablename__ = "resume_chunks"
    
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    resume_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False, index=True)
    candidate_id: Mapped[str] = mapped_column(String(9), nullable=True, index=True)
    section_type: Mapped[SectionType] = mapped_column(SQLEnum(SectionType), nullable=True)
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    chunk_text: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[Vector] = mapped_column(Vector(768), nullable=False)  # Adjust dimension based on model
    metadata_json: Mapped[dict] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
