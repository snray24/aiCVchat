"""
HMAC-SHA256 signed, short-lived tokens for embed chat sessions.

Token format: ``<base64url(json_payload)>.<base64url(hmac)>``
Payload keys: sid, sk, oh, iat, exp, jti.

Secret source: ``EMBED_TOKEN_SECRET`` (falls back to admin token in dev only).

Author: Sanju
Date: 2026-08-06
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
import time
import uuid
from typing import Any, Optional

from app.core.config import settings


def _token_secret() -> bytes:
    """
    Purpose:
        Resolve the HMAC signing key for embed tokens.

    Receives:
        None (reads ``settings.embed_token_secret`` / ``settings.admin_token``).

    Returns:
        bytes: UTF-8 encoded secret material.
    """
    secret = (settings.embed_token_secret or "").strip()
    if not secret:
        # Dev fallback — prefer setting EMBED_TOKEN_SECRET in production
        secret = f"dev-fallback:{settings.admin_token}"
    return secret.encode("utf-8")


def _b64url_encode(raw: bytes) -> str:
    """
    Purpose:
        URL-safe Base64 encode without padding.

    Receives:
        raw (bytes): Input bytes.

    Returns:
        str: Base64url string.
    """
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def _b64url_decode(data: str) -> bytes:
    """
    Purpose:
        Decode URL-safe Base64 (adds padding as needed).

    Receives:
        data (str): Base64url string.

    Returns:
        bytes: Decoded payload.
    """
    pad = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + pad)


def create_embed_token(
    *,
    site_id: str,
    site_key: str,
    origin_host: str,
    ttl_seconds: Optional[int] = None,
) -> tuple[str, int]:
    """
    Purpose:
        Mint a signed session token bound to site + origin host.

    Receives:
        site_id (str): EmbedSite UUID string.
        site_key (str): Public site key.
        origin_host (str): Hostname (optionally with port) of the embedding page.
        ttl_seconds (int | None): Override TTL; default ``EMBED_TOKEN_TTL_SECONDS``.

    Returns:
        tuple[str, int]: ``(token, expires_in_seconds)``.
    """
    ttl = int(ttl_seconds or settings.embed_token_ttl_seconds)
    now = int(time.time())
    payload = {
        "sid": site_id,
        "sk": site_key,
        "oh": origin_host.lower(),
        "iat": now,
        "exp": now + ttl,
        "jti": uuid.uuid4().hex,
    }
    body = _b64url_encode(json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8"))
    sig = _b64url_encode(hmac.new(_token_secret(), body.encode("ascii"), hashlib.sha256).digest())
    return f"{body}.{sig}", ttl


def verify_embed_token(token: str) -> Optional[dict[str, Any]]:
    """
    Purpose:
        Validate HMAC signature and expiry of an embed session token.

    Receives:
        token (str): Full ``body.sig`` string from Authorization Bearer.

    Returns:
        dict[str, Any] | None: Payload with keys sid/sk/oh/iat/exp/jti on success;
        None if missing, malformed, bad signature, or expired.
    """
    if not token or "." not in token:
        return None
    try:
        body, sig = token.rsplit(".", 1)
        expected = _b64url_encode(
            hmac.new(_token_secret(), body.encode("ascii"), hashlib.sha256).digest()
        )
        if not hmac.compare_digest(sig, expected):
            return None
        payload = json.loads(_b64url_decode(body).decode("utf-8"))
        if int(payload.get("exp", 0)) < int(time.time()):
            return None
        return payload
    except Exception:
        return None


def generate_site_key() -> str:
    """
    Purpose:
        Create a new public site key for loader snippets.

    Receives:
        None.

    Returns:
        str: Value like ``aicv_<urlsafe-random>``.
    """
    return "aicv_" + secrets.token_urlsafe(24)
