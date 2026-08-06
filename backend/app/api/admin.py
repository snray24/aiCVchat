"""Admin API endpoint for ingestion and embed site management."""
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Header, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.embed_tokens import generate_site_key
from app.core.logging import logger
from app.db.session import get_db
from app.models.embed_site import EmbedSite
from app.schemas.embed import EmbedSiteCreate, EmbedSiteOut
from app.services.embed_site_service import invalidate_cors_cache, normalize_domain
from app.services.resume_ingestion_service import resume_ingestion_service
from app.api.embed import build_snippet, public_base_url

router = APIRouter()


async def verify_admin_token(x_admin_token: str = Header(None)):
    """Verify admin token for protected endpoints."""
    if x_admin_token != settings.admin_token:
        raise HTTPException(status_code=403, detail="Invalid admin token")
    return True


@router.post("/api/admin/ingest")
async def trigger_ingestion(
    admin_verified: bool = Depends(verify_admin_token),
    db: AsyncSession = Depends(get_db),
):
    """Trigger resume ingestion from local directory."""
    try:
        results = await resume_ingestion_service.ingest_directory(db)
        return {"status": "success", "results": results}
    except Exception as e:
        logger.error(f"Ingestion error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/admin/reindex")
async def trigger_reindex(
    admin_verified: bool = Depends(verify_admin_token),
    db: AsyncSession = Depends(get_db),
):
    """Trigger full re-index (delete and re-ingest all resumes)."""
    try:
        results = await resume_ingestion_service.reindex_all(db)
        return {"status": "success", "results": results}
    except Exception as e:
        logger.error(f"Reindex error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def _site_out(site: EmbedSite, request: Request | None = None) -> EmbedSiteOut:
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
    """Register a domain and issue a unique site key for the embed widget."""
    domain = normalize_domain(body.domain)
    if not domain:
        raise HTTPException(status_code=400, detail="Invalid domain")

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
