"""
Domain/IP validation helpers and short-TTL CORS origin cache for embed sites.

Used by session issuance (``/api/embed/session``), chat auth deps, and
``DynamicCORSMiddleware``.

Author: Sanju
Date: 2026-08-06
"""
from __future__ import annotations

import time
import uuid
from typing import Iterable, Optional, Set
from urllib.parse import urlparse

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.embed_site import EmbedSite

# In-memory cache of allowed CORS origins (full origins like https://example.com)
_cors_cache: Set[str] = set()
_cors_cache_at: float = 0.0
_CORS_TTL = 30.0


def normalize_domain(value: str) -> str:
    """
    Purpose:
        Normalize a URL or host string to a bare lowercase hostname for storage.

    Receives:
        value (str): e.g. ``https://Careers.Acme.com/path``, ``example.com:443``.

    Returns:
        str: Hostname without port/scheme/path, or ``""`` if empty/invalid.
    """
    raw = (value or "").strip().lower()
    if not raw:
        return ""
    if "://" not in raw:
        # host or host:port or path-ish — take before slash
        raw = raw.split("/")[0]
        return raw.split(":")[0]
    parsed = urlparse(raw)
    host = (parsed.hostname or "").lower()
    return host


def normalize_host(value: str) -> str:
    """
    Purpose:
        Normalize Origin/Referer/Host to ``hostname`` or ``hostname:port``.

    Receives:
        value (str): Full origin URL or raw host header.

    Returns:
        str: Comparable host string (non-default ports preserved).
    """
    raw = (value or "").strip().lower()
    if not raw:
        return ""
    if "://" in raw:
        parsed = urlparse(raw)
        host = parsed.hostname or ""
        port = parsed.port
        if port and port not in (80, 443):
            return f"{host}:{port}"
        return host
    # host:port or host
    return raw.split("/")[0]


def origin_from_request_headers(origin: Optional[str], referer: Optional[str]) -> Optional[str]:
    """
    Purpose:
        Resolve the embedding page origin from browser headers.

    Receives:
        origin (str | None): ``Origin`` header.
        referer (str | None): ``Referer`` header (fallback).

    Returns:
        str | None: Absolute origin ``scheme://host[:port]``, or None.
    """
    if origin and origin.strip() and origin.strip() != "null":
        return origin.strip()
    if referer:
        parsed = urlparse(referer.strip())
        if parsed.scheme and parsed.netloc:
            return f"{parsed.scheme}://{parsed.netloc}"
    return None


def host_matches_domain(request_host: str, site_domain: str, allow_subdomains: bool) -> bool:
    """
    Purpose:
        Check whether a request host is allowed for a registered domain.

    Receives:
        request_host (str): From Origin (may include port).
        site_domain (str): Stored EmbedSite.domain.
        allow_subdomains (bool): Allow ``*.domain`` when True.

    Returns:
        bool: True if the host is authorized (includes localhost↔127.0.0.1).
    """
    req = normalize_host(request_host)
    dom = normalize_domain(site_domain)
    if not req or not dom:
        return False

    req_hostname = req.split(":")[0]
    # localhost / 127.0.0.1 equivalence
    aliases = {
        "localhost": {"localhost", "127.0.0.1"},
        "127.0.0.1": {"localhost", "127.0.0.1"},
    }
    if dom in aliases and req_hostname in aliases[dom]:
        return True

    if allow_subdomains:
        return req_hostname == dom or req_hostname.endswith("." + dom)
    return req_hostname == dom


def ip_allowed(client_ip: Optional[str], allowed_ips: Optional[Iterable[str]]) -> bool:
    """
    Purpose:
        Enforce optional client IP allowlist on a site.

    Receives:
        client_ip (str | None): Resolved client address.
        allowed_ips (Iterable[str] | None): Configured allowlist; empty/None = allow all.

    Returns:
        bool: True if the IP may proceed.
    """
    if not allowed_ips:
        return True
    allow = [ip.strip() for ip in allowed_ips if ip and str(ip).strip()]
    if not allow:
        return True
    if not client_ip:
        return False
    return client_ip.strip() in allow


def client_ip_from_request(headers, client_host: Optional[str]) -> Optional[str]:
    """
    Purpose:
        Best-effort client IP behind proxies.

    Receives:
        headers: Mapping with optional ``x-forwarded-for`` / ``x-real-ip``.
        client_host (str | None): Direct TCP peer from ASGI scope.

    Returns:
        str | None: First forwarded IP, real-ip, or peer host.
    """
    forwarded = (headers.get("x-forwarded-for") or "").split(",")[0].strip()
    if forwarded:
        return forwarded
    real_ip = (headers.get("x-real-ip") or "").strip()
    if real_ip:
        return real_ip
    return client_host


async def get_site_by_key(db: AsyncSession, site_key: str) -> Optional[EmbedSite]:
    """
    Purpose:
        Load an active EmbedSite by public site key.

    Receives:
        db (AsyncSession): DB session.
        site_key (str): Public key from the widget.

    Returns:
        EmbedSite | None: Active row, or None if missing/inactive.
    """
    result = await db.execute(
        select(EmbedSite).where(EmbedSite.site_key == site_key, EmbedSite.is_active.is_(True))
    )
    return result.scalar_one_or_none()


async def is_site_active(db: AsyncSession, site_id: str) -> bool:
    """
    Purpose:
        Confirm a site UUID is still active (used on each chat request).

    Receives:
        db (AsyncSession): DB session.
        site_id (str): UUID string from token payload ``sid``.

    Returns:
        bool: True if an active row exists.
    """
    try:
        sid = uuid.UUID(str(site_id))
    except Exception:
        return False
    result = await db.execute(
        select(EmbedSite.id).where(
            EmbedSite.id == sid,
            EmbedSite.is_active.is_(True),
        )
    )
    return result.scalar_one_or_none() is not None


def static_frontend_origins() -> Set[str]:
    """
    Purpose:
        Parse ``FRONTEND_ORIGIN`` into a set of full origins (with localhost variants).

    Receives:
        None (reads settings).

    Returns:
        set[str]: Origins always allowed for CORS (e.g. Next.js app).
    """
    origins: Set[str] = set()
    for origin in settings.frontend_origin.split(","):
        o = origin.strip()
        if not o:
            continue
        origins.add(o)
        if o.startswith("http://localhost"):
            origins.add(o.replace("localhost", "127.0.0.1"))
        elif o.startswith("http://127.0.0.1"):
            origins.add(o.replace("127.0.0.1", "localhost"))
    return origins


def invalidate_cors_cache() -> None:
    """
    Purpose:
        Force the next CORS lookup to rebuild from DB (call after admin writes).

    Receives:
        None.

    Returns:
        None.
    """
    global _cors_cache_at
    _cors_cache_at = 0.0


async def refresh_cors_origins(db: AsyncSession) -> Set[str]:
    """
    Purpose:
        Rebuild the in-memory set of allowed CORS origins from active sites.

    Receives:
        db (AsyncSession): DB session.

    Returns:
        set[str]: Full origins (http/https) for FRONTEND_ORIGIN + embed domains.
    """
    global _cors_cache, _cors_cache_at
    origins = set(static_frontend_origins())
    result = await db.execute(select(EmbedSite).where(EmbedSite.is_active.is_(True)))
    sites = result.scalars().all()
    for site in sites:
        host = normalize_domain(site.domain)
        if not host:
            continue
        # Allow both http and https for registered hosts (local + prod)
        origins.add(f"https://{host}")
        origins.add(f"http://{host}")
        if host in ("localhost", "127.0.0.1"):
            for port in ("3000", "8000", "5173"):
                origins.add(f"http://localhost:{port}")
                origins.add(f"http://127.0.0.1:{port}")
    _cors_cache = origins
    _cors_cache_at = time.monotonic()
    return origins


async def get_cached_cors_origins(db: Optional[AsyncSession] = None) -> Set[str]:
    """
    Purpose:
        Return cached CORS origins, refreshing when TTL expires.

    Receives:
        db (AsyncSession | None): Needed to refresh; if None, returns stale/static set.

    Returns:
        set[str]: Allowed origins.
    """
    global _cors_cache, _cors_cache_at
    now = time.monotonic()
    if _cors_cache and (now - _cors_cache_at) < _CORS_TTL:
        return _cors_cache
    if db is None:
        return _cors_cache or static_frontend_origins()
    return await refresh_cors_origins(db)


def origin_allowed_sync(origin: str, allowed: Set[str]) -> bool:
    """
    Purpose:
        Sync check whether a browser Origin is in the allow set (exact or same host).

    Receives:
        origin (str): Request Origin header value.
        allowed (set[str]): Cached allowed origins.

    Returns:
        bool: True if CORS should echo this Origin.
    """
    if not origin:
        return False
    if origin in allowed:
        return True
    # Also allow if host matches any registered origin host
    host = normalize_host(origin)
    for allowed_origin in allowed:
        if normalize_host(allowed_origin) == host:
            return True
    return False
