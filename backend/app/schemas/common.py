"""Common schemas."""
from uuid import UUID
from pydantic import BaseModel


class UUIDModel(BaseModel):
    """Base model with UUID."""
    id: UUID


class TimestampModel(BaseModel):
    """Base model with timestamps."""
    created_at: str
    updated_at: str | None = None
