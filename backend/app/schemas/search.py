"""Search schemas."""
from typing import Optional, List
from pydantic import BaseModel, Field
from app.schemas.chat import ChatFilters, CandidateMatch


class SearchRequest(BaseModel):
    """Search API request."""
    query: str = Field(..., min_length=1, description="Search query")
    filters: Optional[ChatFilters] = Field(None, description="Search filters")
    top_k: Optional[int] = Field(8, ge=1, le=20, description="Number of results")


class SearchResponse(BaseModel):
    """Search API response."""
    matches: List[CandidateMatch]
    total: int
