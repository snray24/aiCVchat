"""
SQLAlchemy model for websites authorized to embed the AiCV chat widget.

Each row stores a unique public ``site_key``, the registered hostname, optional
IP allowlist, and rate-limit settings used by session issuance and CORS.

Author: Sanju
Date: 2026-08-06
"""
import uuid
from datetime import datetime
from typing import Optional, List

from sqlalchemy import String, Boolean, DateTime, Integer, JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class EmbedSite(Base):
    """
    Purpose:
        Persist one registered embed customer (domain + site key).

    Table:
        ``embed_sites``

    Fields (types):
        id (UUID): Primary key.
        site_key (str): Public key baked into loader snippets (e.g. ``aicv_…``).
        name (str): Human-friendly label for ops.
        domain (str): Normalized hostname only (no scheme/path), e.g. ``example.com``.
        allow_subdomains (bool): If True, ``*.domain`` may obtain sessions.
        allowed_ips (list[str] | None): Client IP allowlist; empty/None = any IP.
        is_active (bool): False after revoke; blocks sessions and CORS.
        rate_limit_per_minute (int): Per-site session/chat budget override.
        created_at (datetime): Registration time (UTC).
        revoked_at (datetime | None): Set when deactivated.
    """

    __tablename__ = "embed_sites"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    site_key: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    # Normalized hostname only (e.g. example.com or localhost) — no scheme/path
    domain: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    allow_subdomains: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    # Optional client IP allowlist; empty/null = any IP
    allowed_ips: Mapped[Optional[List]] = mapped_column(JSON, nullable=True, default=list)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, index=True)
    rate_limit_per_minute: Mapped[int] = mapped_column(Integer, nullable=False, default=60)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    revoked_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
