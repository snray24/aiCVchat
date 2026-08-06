"""Dynamic embed snippet / loader generation and session issuance."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import JSONResponse, PlainTextResponse, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.embed_tokens import create_embed_token
from app.core.logging import logger
from app.core.rate_limit import ip_limiter, site_limiter
from app.db.session import get_db
from app.schemas.embed import EmbedSessionRequest, EmbedSessionResponse
from app.services.embed_site_service import (
    client_ip_from_request,
    get_site_by_key,
    host_matches_domain,
    ip_allowed,
    normalize_host,
    origin_from_request_headers,
)

router = APIRouter(tags=["embed"])


def public_base_url(request: Request) -> str:
    """Resolve the externally visible API origin from the request."""
    forwarded_proto = (request.headers.get("x-forwarded-proto") or "").split(",")[0].strip()
    forwarded_host = (request.headers.get("x-forwarded-host") or "").split(",")[0].strip()
    host = forwarded_host or request.headers.get("host") or request.url.netloc
    scheme = forwarded_proto or request.url.scheme or "http"
    return f"{scheme}://{host}".rstrip("/")


def build_snippet(
    base: str,
    *,
    site_key: str | None = None,
    open_on_load: bool = False,
    position: str = "right",
) -> str:
    """Minimal one-tag snippet — loader injects config + widget automatically."""
    qs = []
    if site_key:
        qs.append(f"key={site_key}")
    if open_on_load:
        qs.append("openOnLoad=1")
    if position and position != "right":
        qs.append(f"position={position}")
    query = ("?" + "&".join(qs)) if qs else ""
    return f'<script src="{base}/embed/loader.js{query}" async></script>'


def build_loader_js(
    base: str,
    *,
    site_key: str | None = None,
    open_on_load: bool = False,
    position: str = "right",
) -> str:
    """JS that sets apiBaseUrl (+ optional siteKey) and loads config + widget."""
    open_js = "true" if open_on_load else "false"
    position_js = position.replace("\\", "\\\\").replace("'", "\\'")
    site_key_js = (site_key or "").replace("\\", "\\\\").replace("'", "\\'")
    return f"""/*! AiCV Chat dynamic loader — generated */
(function (g) {{
  "use strict";
  var API_BASE = {base!r};
  var SITE_KEY = '{site_key_js}';
  var cfg = g.AiCVChatConfig = Object.assign({{
    apiBaseUrl: API_BASE,
    position: '{position_js}',
    openOnLoad: {open_js}
  }}, g.AiCVChatConfig || {{}});
  if (!cfg.apiBaseUrl) cfg.apiBaseUrl = API_BASE;
  if (SITE_KEY) cfg.siteKey = SITE_KEY;

  function loadScript(src, next) {{
    var s = g.document.createElement("script");
    s.src = src;
    s.async = false;
    s.onload = function () {{ if (next) next(); }};
    s.onerror = function () {{
      if (g.console && console.error) console.error("[AiCVChat] failed to load", src);
    }};
    (g.document.head || g.document.documentElement).appendChild(s);
  }}

  loadScript(API_BASE + "/embed/config.js", function () {{
    loadScript(API_BASE + "/embed/aicvchat-widget.js");
  }});
}})(typeof window !== "undefined" ? window : globalThis);
"""


@router.get("/api/embed/snippet")
async def embed_snippet_api(
    request: Request,
    format: str = Query("json", pattern="^(json|html|text)$"),
    openOnLoad: bool = Query(False),
    position: str = Query("right", pattern="^(right|left)$"),
    key: str | None = Query(None, description="Registered site key"),
):
    """Return a ready-to-paste embed snippet with this server's public URL filled in."""
    base = public_base_url(request)
    snippet = build_snippet(
        base, site_key=key, open_on_load=openOnLoad, position=position
    )
    loader_url = f"{base}/embed/loader.js"
    parts = []
    if key:
        parts.append(f"key={key}")
    if openOnLoad:
        parts.append("openOnLoad=1")
    if position != "right":
        parts.append(f"position={position}")
    if parts:
        loader_url += "?" + "&".join(parts)

    instructions = (
        "Paste the snippet before </body>. "
        "Register the host domain via POST /api/admin/embed-sites to obtain a site key, "
        "then pass ?key=YOUR_SITE_KEY (required when EMBED_AUTH_REQUIRED=true)."
    )

    if format in ("html", "text"):
        return PlainTextResponse(
            snippet + "\n",
            media_type="text/plain; charset=utf-8",
            headers={"Cache-Control": "no-store"},
        )

    return JSONResponse(
        {
            "api_base_url": base,
            "loader_url": loader_url,
            "snippet": snippet,
            "site_key": key,
            "full_snippet": (
                f"<!-- AiCV Chat: auto-generated — register domain + site key required -->\n{snippet}"
            ),
            "instructions": instructions,
        },
        headers={"Cache-Control": "no-store"},
    )


@router.get("/api/embed/loader.js")
@router.get("/embed/loader.js")
async def embed_loader_js(
    request: Request,
    openOnLoad: bool = Query(False),
    position: str = Query("right", pattern="^(right|left)$"),
    key: str | None = Query(None, description="Registered site key"),
):
    """One-line script src target: dynamically injects widget with correct API base."""
    base = public_base_url(request)
    js = build_loader_js(
        base, site_key=key, open_on_load=openOnLoad, position=position
    )
    return Response(
        content=js,
        media_type="application/javascript; charset=utf-8",
        headers={
            "Cache-Control": "public, max-age=60",
            "X-AiCVChat-Api-Base": base,
        },
    )


@router.post("/api/embed/session", response_model=EmbedSessionResponse)
async def create_embed_session(
    body: EmbedSessionRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Issue a short-lived session token bound to site_key + Origin host."""
    if settings.require_https_for_embed:
        proto = (
            (request.headers.get("x-forwarded-proto") or request.url.scheme or "http")
            .split(",")[0]
            .strip()
            .lower()
        )
        if proto != "https":
            raise HTTPException(status_code=403, detail="HTTPS required for embed sessions")

    client_ip = client_ip_from_request(
        request.headers,
        request.client.host if request.client else None,
    )
    if not ip_limiter.allow(f"session-ip:{client_ip or 'unknown'}", settings.embed_rate_limit_per_minute):
        raise HTTPException(status_code=429, detail="Rate limit exceeded (IP)")

    site = await get_site_by_key(db, body.site_key.strip())
    if not site:
        raise HTTPException(status_code=403, detail="Invalid or inactive site key")

    if not site_limiter.allow(
        f"session-site:{site.site_key}",
        site.rate_limit_per_minute or settings.embed_site_rate_limit_per_minute,
    ):
        raise HTTPException(status_code=429, detail="Rate limit exceeded (site)")

    if not ip_allowed(client_ip, site.allowed_ips):
        logger.warning(f"Embed session denied: IP {client_ip} not allowlisted for {site.domain}")
        raise HTTPException(status_code=403, detail="Client IP not allowed for this site key")

    origin = origin_from_request_headers(
        request.headers.get("origin"),
        request.headers.get("referer"),
    )
    if not origin:
        # Same-origin file/demo fallback: use Host header as http(s)://host
        host = request.headers.get("host")
        if host:
            scheme = (
                (request.headers.get("x-forwarded-proto") or request.url.scheme or "http")
                .split(",")[0]
                .strip()
            )
            origin = f"{scheme}://{host}"
        else:
            raise HTTPException(status_code=403, detail="Missing Origin/Referer")

    origin_host = normalize_host(origin)
    if not host_matches_domain(origin_host, site.domain, site.allow_subdomains):
        logger.warning(
            f"Embed session denied: origin host {origin_host} != registered {site.domain}"
        )
        raise HTTPException(
            status_code=403,
            detail="Origin domain does not match the registered site key",
        )

    token, ttl = create_embed_token(
        site_id=str(site.id),
        site_key=site.site_key,
        origin_host=origin_host.split(":")[0],
    )
    base = public_base_url(request)
    return EmbedSessionResponse(
        access_token=token,
        expires_in=ttl,
        api_base_url=base,
    )
