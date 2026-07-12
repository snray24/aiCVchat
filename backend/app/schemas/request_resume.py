"""Resume request schemas."""
from typing import List
from pydantic import BaseModel, Field


class RequestResumeRequest(BaseModel):
    """Request resume access."""
    email: str = Field(..., description="Requester email address")
    resume_ids: List[str] = Field(..., min_items=1, max_items=10, description="Resume IDs to request")


class RequestResumeResponse(BaseModel):
    """Resume request response."""
    status: str = Field(..., description="accepted, denied, or failed")
    message: str = Field(..., description="Status message")
