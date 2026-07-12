"""Chat schemas."""
from typing import Optional, List
from pydantic import BaseModel, Field


class ChatFilters(BaseModel):
    """Filters for chat search."""
    skills: Optional[str] = Field(None, description="Comma-separated skill keywords")
    min_years_experience: Optional[int] = Field(None, ge=0)
    current_title: Optional[str] = Field(None, description="Job title keyword")
    education: Optional[str] = Field(None, description="Education keyword")
    location: Optional[str] = Field(None, description="Location keyword")


class ChatMessage(BaseModel):
    """Single chat message."""
    role: str = Field(..., description="user or assistant")
    content: str = Field(..., description="Message content")


class ChatRequest(BaseModel):
    """Chat API request."""
    message: str = Field(..., min_length=1, description="User message")
    filters: Optional[ChatFilters] = Field(None, description="Search filters")
    history: Optional[List[ChatMessage]] = Field(default_factory=list, description="Conversation history")


class CandidateMatch(BaseModel):
    """Candidate match result."""
    resume_id: str
    full_name: str
    current_title: str | None
    years_experience: int | None
    top_skills: List[str]
    short_match_reason: str


class ChatResponse(BaseModel):
    """Chat API response."""
    answer: str
    matches: List[CandidateMatch]
    email_required: bool = True
