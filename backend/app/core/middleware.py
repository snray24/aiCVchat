"""
ASGI middleware: security response headers and dynamic CORS for embed sites.

Registered in ``main.py`` (outermost middleware runs first on the request).

Author: Sanju
Date: 2026-08-06
"""
from __future__ import annotations

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.core.config import settings
from app.core.logging import logger
from app.services.embed_site_service import (
    get_cached_cors_origins,
    origin_allowed_sync,
    static_frontend_origins,
)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Purpose:
        Attach baseline browser security headers to every response.
    """

    async def dispatch(self, request: Request, call_next):
        """
        Purpose:
            Continue the chain, then set security headers if missing.

        Receives:
            request (Request): Incoming request.
            call_next: Next ASGI handler.

        Returns:
            Response: Downstream response with headers such as
            ``X-Content-Type-Options``, ``Referrer-Policy``, ``Permissions-Policy``,
            ``X-Frame-Options``, and optionally HSTS when HTTPS is required.
        """
        response: Response = await call_next(request)
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        response.headers.setdefault(
            "Permissions-Policy", "geolocation=(), microphone=(), camera=()"
        )
        response.headers.setdefault("X-Frame-Options", "SAMEORIGIN")
        if settings.require_https_for_embed:
            response.headers.setdefault(
                "Strict-Transport-Security", "max-age=31536000; includeSubDomains"
            )
        return response


class DynamicCORSMiddleware(BaseHTTPMiddleware):
    """
    Purpose:
        Echo ``Access-Control-Allow-Origin`` only for FRONTEND_ORIGIN and
        registered embed domains. Emergency mode: ``CORS_ALLOW_ANY_ORIGIN=*``.
    """

    async def dispatch(self, request: Request, call_next):
        """
        Purpose:
            Handle CORS preflight and attach allow-origin on real responses.

        Receives:
            request (Request): May include ``Origin`` and preflight headers.
            call_next: Next ASGI handler.

        Returns:
            Response: 204 preflight when allowed; 403 when Origin denied;
            otherwise the app response with CORS headers when Origin is allowed.
        """
        origin = (request.headers.get("origin") or "").strip()

        if settings.cors_allow_any_origin:
            if request.method == "OPTIONS":
                return self._preflight(origin or "*", allow_any=True)
            response = await call_next(request)
            response.headers["Access-Control-Allow-Origin"] = "*"
            response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, PATCH, DELETE, OPTIONS"
            response.headers["Access-Control-Allow-Headers"] = (
                request.headers.get("access-control-request-headers")
                or "Authorization, Content-Type, X-Admin-Token, Accept"
            )
            return response

        allowed = static_frontend_origins()
        try:
            from app.db.session import AsyncSessionLocal

            async with AsyncSessionLocal() as db:
                allowed = await get_cached_cors_origins(db)
        except Exception as e:
            logger.debug(f"CORS origin cache refresh skipped: {e}")
            allowed = allowed or static_frontend_origins()

        allow = bool(origin) and origin_allowed_sync(origin, allowed)

        if request.method == "OPTIONS":
            if not allow:
                return Response(status_code=403, content="CORS origin denied")
            return self._preflight(origin, allow_any=False)

        response = await call_next(request)
        if allow:
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Vary"] = "Origin"
            response.headers["Access-Control-Allow-Methods"] = (
                "GET, POST, PUT, PATCH, DELETE, OPTIONS"
            )
            response.headers["Access-Control-Allow-Headers"] = (
                "Authorization, Content-Type, X-Admin-Token, Accept"
            )
        return response

    @staticmethod
    def _preflight(origin: str, *, allow_any: bool) -> Response:
        """
        Purpose:
            Build a CORS preflight (OPTIONS) response.

        Receives:
            origin (str): Value for Allow-Origin (or ``*`` when allow_any).
            allow_any (bool): If True, use wildcard origin.

        Returns:
            Response: HTTP 204 with CORS allow headers.
        """
        headers = {
            "Access-Control-Allow-Methods": "GET, POST, PUT, PATCH, DELETE, OPTIONS",
            "Access-Control-Allow-Headers": (
                "Authorization, Content-Type, X-Admin-Token, Accept"
            ),
            "Access-Control-Max-Age": "600",
        }
        if allow_any:
            headers["Access-Control-Allow-Origin"] = "*"
        else:
            headers["Access-Control-Allow-Origin"] = origin
            headers["Vary"] = "Origin"
        return Response(status_code=204, headers=headers)
