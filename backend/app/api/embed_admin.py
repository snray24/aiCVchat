"""
Admin APIs for embed site registration (domain + site key).

Separate from legacy ``admin.py`` ingest/reindex so pre-existing admin
behaviour is unchanged. Reuses ``verify_admin_token`` from admin.

Author: Sanju
Date: 2026-08-06
"""
from __future__ import annotations

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.admin import verify_admin_token
from app.api.embed import build_snippet, public_base_url
from app.core.config import settings
from app.core.embed_tokens import generate_site_key
from app.core.logging import logger
from app.db.session import get_db
from app.models.embed_site import EmbedSite
from app.schemas.embed import EmbedSiteCreate, EmbedSiteOut
from app.services.embed_site_service import (
    invalidate_cors_cache,
    is_safe_registered_domain,
    normalize_domain,
)

router = APIRouter(tags=["embed-admin"])


def _site_out(site: EmbedSite, request: Request | None = None) -> EmbedSiteOut:
    """
    Purpose:
        Map EmbedSite ORM row to API response, optionally with install snippet.

    Receives:
        site (EmbedSite): DB row.
        request (Request | None): Used to build absolute loader URL.

    Returns:
        EmbedSiteOut: Serialisable site + optional snippet HTML.
    """
    snippet = None
    if request is not None and site.is_active:
        base = public_base_url(request)
        snippet = build_snippet(base, site_key=site.site_key)
    return EmbedSiteOut(
        id=site.id,
        site_key=site.site_key,
        name=site.name,
        domain=site.domain,
        allow_subdomains=site.allow_subdomains,
        allowed_ips=site.allowed_ips,
        is_active=site.is_active,
        rate_limit_per_minute=site.rate_limit_per_minute,
        created_at=site.created_at,
        revoked_at=site.revoked_at,
        snippet=snippet,
    )


@router.post("/api/admin/embed-sites", response_model=EmbedSiteOut)
async def create_embed_site(
    body: EmbedSiteCreate,
    request: Request,
    admin_verified: bool = Depends(verify_admin_token),
    db: AsyncSession = Depends(get_db),
):
    """
    Purpose:
        Register a hostname and issue a unique public site key.

    Receives:
        body (EmbedSiteCreate): name, domain, allow_subdomains, allowed_ips, rate_limit.
        X-Admin-Token header.

    Returns:
        EmbedSiteOut including ``site_key`` and install ``snippet``.
    """
    domain = normalize_domain(body.domain)
    if not domain or not is_safe_registered_domain(domain):
        raise HTTPException(
            status_code=400,
            detail="Invalid domain — use a hostname like example.com (not a bare TLD)",
        )

    site = EmbedSite(
        site_key=generate_site_key(),
        name=body.name.strip(),
        domain=domain,
        allow_subdomains=body.allow_subdomains,
        allowed_ips=body.allowed_ips or [],
        is_active=True,
        rate_limit_per_minute=(
            body.rate_limit_per_minute
            if body.rate_limit_per_minute is not None
            else settings.embed_site_rate_limit_per_minute
        ),
    )
    db.add(site)
    await db.commit()
    await db.refresh(site)
    invalidate_cors_cache()
    logger.info(f"Registered embed site {site.domain} key={site.site_key[:12]}…")
    return _site_out(site, request)


@router.get("/api/admin/embed-sites", response_model=list[EmbedSiteOut])
async def list_embed_sites(
    request: Request,
    admin_verified: bool = Depends(verify_admin_token),
    db: AsyncSession = Depends(get_db),
):
    """
    Purpose:
        List all registered embed sites (active and revoked).

    Returns:
        list[EmbedSiteOut]
    """
    result = await db.execute(select(EmbedSite).order_by(EmbedSite.created_at.desc()))
    sites = result.scalars().all()
    return [_site_out(s, request) for s in sites]


@router.post("/api/admin/embed-sites/{site_id}/revoke", response_model=EmbedSiteOut)
async def revoke_embed_site(
    site_id: UUID,
    request: Request,
    admin_verified: bool = Depends(verify_admin_token),
    db: AsyncSession = Depends(get_db),
):
    """
    Purpose:
        Deactivate a site key (blocks new sessions and invalidates CORS entry).

    Receives:
        site_id (UUID): Embed site primary key.

    Returns:
        EmbedSiteOut with is_active=False.
    """
    site = await db.get(EmbedSite, site_id)
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")
    site.is_active = False
    site.revoked_at = datetime.utcnow()
    await db.commit()
    await db.refresh(site)
    invalidate_cors_cache()
    return _site_out(site, request)


@router.post("/api/admin/embed-sites/{site_id}/rotate-key", response_model=EmbedSiteOut)
async def rotate_embed_site_key(
    site_id: UUID,
    request: Request,
    admin_verified: bool = Depends(verify_admin_token),
    db: AsyncSession = Depends(get_db),
):
    """
    Purpose:
        Issue a new site_key; old keys and sessions fail thereafter.

    Receives:
        site_id (UUID): Active embed site id.

    Returns:
        EmbedSiteOut with the new ``site_key`` and snippet.
    """
    site = await db.get(EmbedSite, site_id)
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")
    if not site.is_active:
        raise HTTPException(status_code=400, detail="Site is revoked; create a new registration")
    site.site_key = generate_site_key()
    await db.commit()
    await db.refresh(site)
    invalidate_cors_cache()
    logger.info(f"Rotated embed site key for {site.domain}")
    return _site_out(site, request)
