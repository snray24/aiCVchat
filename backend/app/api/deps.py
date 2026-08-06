"""
FastAPI dependencies that gate **embed-only** routes behind session tokens.

Wire with: ``Depends(require_embed_session)`` on ``/api/embed/*`` protected routes
(e.g. ``/api/embed/chat``, ``/api/embed/search``).

Does **not** apply to legacy ``/api/chat``, ``/api/search``, or ``/api/request-resumes``.
When ``EMBED_AUTH_REQUIRED=false``, the dependency is a no-op (local break-glass).

Author: Sanju
Date: 2026-08-06
"""
from __future__ import annotations

import hmac

from fastapi import Depends, Header, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.embed_tokens import verify_embed_token
from app.core.rate_limit import ip_limiter, site_limiter
from app.db.session import get_db
from app.services.embed_site_service import (
    client_ip_from_request,
    get_site_by_id,
    normalize_host,
    origin_from_request_headers,
)


def _request_scheme(request: Request) -> str:
    if settings.trust_proxy:
        return (
            (request.headers.get("x-forwarded-proto") or request.url.scheme or "http")
            .split(",")[0]
            .strip()
            .lower()
        )
    return (request.url.scheme or "http").lower()


async def require_embed_session(
    request: Request,
    authorization: str | None = Header(None),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Purpose:
        Validate Bearer embed session, Origin binding, site activity, and rate limits
        before allowing embed-only routes (``/api/embed/chat``, ``/api/embed/search``).

    Receives:
        request (Request): Incoming HTTP request (scheme, client, headers).
        authorization (str | None): ``Authorization`` header, expected
            ``Bearer <access_token>``.
        db (AsyncSession): Injected DB session for revoke / key-rotate checks.

    Returns:
        dict: Token payload plus ``site`` metadata used by callers, or
        ``{\"auth_disabled\": True}`` when embed auth is turned off.

    Raises:
        HTTPException 401: Missing/invalid/expired token or rotated site key.
        HTTPException 403: HTTPS required, missing/mismatched Origin, or revoked site.
        HTTPException 429: IP or site rate limit exceeded.
    """
    if not settings.embed_auth_required:
        return {"auth_disabled": True}

    if settings.require_https_for_embed and _request_scheme(request) != "https":
        raise HTTPException(status_code=403, detail="HTTPS required for embed chat")

    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Missing embed session token")

    token = authorization.split(" ", 1)[1].strip()
    payload = verify_embed_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired embed session token")

    site_id = str(payload.get("sid") or "")
    token_site_key = str(payload.get("sk") or "")
    token_host = str(payload.get("oh") or "").lower()

    # Require browser Origin/Referer — do not skip binding for curl-style callers
    origin = origin_from_request_headers(
        request.headers.get("origin"),
        request.headers.get("referer"),
    )
    if not origin:
        raise HTTPException(
            status_code=403,
            detail="Missing Origin/Referer — embed chat must be called from a browser page",
        )

    req_host = normalize_host(origin)
    req_hostname = req_host.split(":")[0]
    token_hostname = token_host.split(":")[0]
    aliases = {"localhost", "127.0.0.1"}
    hosts_match = req_hostname == token_hostname or (
        req_hostname in aliases and token_hostname in aliases
    )
    if not hosts_match:
        raise HTTPException(status_code=403, detail="Origin does not match session")

    site = await get_site_by_id(db, site_id)
    if not site:
        raise HTTPException(status_code=403, detail="Embed site revoked or inactive")

    # Invalidate sessions after key rotation
    if not hmac.compare_digest(site.site_key, token_site_key):
        raise HTTPException(status_code=401, detail="Site key rotated — refresh embed session")

    client_ip = client_ip_from_request(
        request.headers,
        request.client.host if request.client else None,
    )
    if not ip_limiter.allow(f"ip:{client_ip or 'unknown'}", settings.embed_rate_limit_per_minute):
        raise HTTPException(status_code=429, detail="Rate limit exceeded (IP)")

    site_limit = site.rate_limit_per_minute or settings.embed_site_rate_limit_per_minute
    if not site_limiter.allow(f"site:{site.site_key}", site_limit):
        raise HTTPException(status_code=429, detail="Rate limit exceeded (site)")

    payload["site_rate_limit"] = site_limit
    return payload
