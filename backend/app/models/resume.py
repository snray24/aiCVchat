"""Resume model."""
import uuid
from datetime import datetime
from sqlalchemy import String, Text, Integer, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from pgvector.sqlalchemy import Vector
from app.db.base import Base


class Resume(Base):
    """Resume model representing a candidate's resume."""
    
    __tablename__ = "resumes"
    
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    current_title: Mapped[str] = mapped_column(String(255), nullable=True)
    total_years_experience: Mapped[int] = mapped_column(Integer, nullable=True)
    summary: Mapped[str] = mapped_column(Text, nullable=True)
    skills_text: Mapped[str] = mapped_column(Text, nullable=True)
    education_text: Mapped[str] = mapped_column(Text, nullable=True)
    certifications_text: Mapped[str] = mapped_column(Text, nullable=True)
    last_company: Mapped[str] = mapped_column(String(255), nullable=True)
    location: Mapped[str] = mapped_column(String(255), nullable=True)
    source_file_name: Mapped[str] = mapped_column(String(512), nullable=False)
    source_file_path: Mapped[str] = mapped_column(String(512), nullable=False)
    extracted_text: Mapped[str] = mapped_column(Text, nullable=False)
    file_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
