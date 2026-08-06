"""
Pydantic request/response schemas for embed site admin APIs and session minting.

Used by:
    - ``POST/GET /api/admin/embed-sites`` (create/list)
    - ``POST /api/embed/session`` (widget bootstrap)

Author: Sanju
Date: 2026-08-06
"""
from __future__ import annotations

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class EmbedSiteCreate(BaseModel):
    """
    Purpose:
        Body for registering a new embed site.

    Receives (JSON):
        name (str): Display name, 1–255 chars.
        domain (str): Hostname or URL; server normalizes to hostname.
        allow_subdomains (bool, optional): Default False.
        allowed_ips (list[str] | null, optional): Client IPs; empty = any.
        rate_limit_per_minute (int | null, optional): 1–1000; null uses global default.

    Output:
        Validated EmbedSiteCreate instance (not returned to client directly).
    """

    name: str = Field(..., min_length=1, max_length=255)
    domain: str = Field(..., min_length=1, max_length=255, description="Hostname only, e.g. example.com")
    allow_subdomains: bool = False
    allowed_ips: Optional[List[str]] = Field(
        default=None,
        description="Optional client IP allowlist; empty means any IP",
    )
    rate_limit_per_minute: Optional[int] = Field(None, ge=1, le=1000)


class EmbedSiteOut(BaseModel):
    """
    Purpose:
        Public representation of a registered embed site (admin responses).

    Receives:
        Built from EmbedSite ORM row (+ optional snippet string).

    Output (JSON):
        id (UUID), site_key (str), name (str), domain (str),
        allow_subdomains (bool), allowed_ips (list[str] | null),
        is_active (bool), rate_limit_per_minute (int),
        created_at (datetime), revoked_at (datetime | null),
        snippet (str | null): Ready-to-paste ``<script src=…loader.js?key=…>``.
    """

    id: UUID
    site_key: str
    name: str
    domain: str
    allow_subdomains: bool
    allowed_ips: Optional[List[str]] = None
    is_active: bool
    rate_limit_per_minute: int
    created_at: datetime
    revoked_at: Optional[datetime] = None
    snippet: Optional[str] = None

    class Config:
        from_attributes = True


class EmbedSessionRequest(BaseModel):
    """
    Purpose:
        Body for ``POST /api/embed/session``.

    Receives (JSON):
        site_key (str): Public key from registration (min 8, max 64 chars).

    Note:
        Browser Origin/Referer are read from HTTP headers, not this body.
    """

    site_key: str = Field(..., min_length=8, max_length=64)


class EmbedSessionResponse(BaseModel):
    """
    Purpose:
        Short-lived access token returned after domain/IP validation.

    Output (JSON):
        access_token (str): HMAC-signed bearer token for /api/chat and /api/search.
        expires_in (int): Seconds until expiry.
        api_base_url (str): Absolute API origin for the widget.
        token_type (str): Always ``Bearer``.
    """

    access_token: str
    expires_in: int
    api_base_url: str
    token_type: str = "Bearer"
