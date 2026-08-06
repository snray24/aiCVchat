"""
FastAPI dependencies that gate chat/search behind embed session tokens.

Wire with: ``Depends(require_embed_session)`` on protected routes.
When ``EMBED_AUTH_REQUIRED=false``, the dependency is a no-op (local break-glass).

Author: Sanju
Date: 2026-08-06
"""
from __future__ import annotations

from fastapi import Depends, Header, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.embed_tokens import verify_embed_token
from app.core.rate_limit import ip_limiter, site_limiter
from app.db.session import get_db
from app.services.embed_site_service import (
    client_ip_from_request,
    is_site_active,
    normalize_host,
    origin_from_request_headers,
)


async def require_embed_session(
    request: Request,
    authorization: str | None = Header(None),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Purpose:
        Validate Bearer embed session, Origin binding, site activity, and rate limits
        before allowing ``/api/chat`` or ``/api/search``.

    Receives:
        request (Request): Incoming HTTP request (scheme, client, headers).
        authorization (str | None): ``Authorization`` header, expected
            ``Bearer <access_token>``.
        db (AsyncSession): Injected DB session for revoke checks.

    Returns:
        dict: Token payload (``sid``, ``sk``, ``oh``, ``iat``, ``exp``, ``jti``)
        or ``{\"auth_disabled\": True}`` when embed auth is turned off.

    Raises:
        HTTPException 401: Missing/invalid/expired token.
        HTTPException 403: HTTPS required, origin mismatch, or revoked site.
        HTTPException 429: IP or site rate limit exceeded.
    """
    if not settings.embed_auth_required:
        return {"auth_disabled": True}

    if settings.require_https_for_embed:
        proto = (
            (request.headers.get("x-forwarded-proto") or request.url.scheme or "http")
            .split(",")[0]
            .strip()
            .lower()
        )
        if proto != "https":
            raise HTTPException(status_code=403, detail="HTTPS required for embed chat")

    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Missing embed session token")

    token = authorization.split(" ", 1)[1].strip()
    payload = verify_embed_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired embed session token")

    site_id = str(payload.get("sid") or "")
    site_key = str(payload.get("sk") or "")
    token_host = str(payload.get("oh") or "").lower()

    origin = origin_from_request_headers(
        request.headers.get("origin"),
        request.headers.get("referer"),
    )
    if origin:
        req_host = normalize_host(origin)
        if req_host and token_host and req_host.split(":")[0] != token_host.split(":")[0]:
            # Allow localhost alias mismatch already handled at issue time; strict host check
            aliases = {"localhost", "127.0.0.1"}
            a, b = req_host.split(":")[0], token_host.split(":")[0]
            if not (a in aliases and b in aliases):
                if a != b:
                    raise HTTPException(status_code=403, detail="Origin does not match session")

    if not await is_site_active(db, site_id):
        raise HTTPException(status_code=403, detail="Embed site revoked or inactive")

    client_ip = client_ip_from_request(
        request.headers,
        request.client.host if request.client else None,
    )
    if not ip_limiter.allow(f"ip:{client_ip or 'unknown'}", settings.embed_rate_limit_per_minute):
        raise HTTPException(status_code=429, detail="Rate limit exceeded (IP)")
    if site_key and not site_limiter.allow(
        f"site:{site_key}", settings.embed_site_rate_limit_per_minute
    ):
        raise HTTPException(status_code=429, detail="Rate limit exceeded (site)")

    return payload
