"""
CLI helper: register an embed domain via the admin API and print the snippet.

Usage:
    python scripts/register_embed_site.py --name "Acme" --domain careers.acme.com

Requires a running backend and valid ``ADMIN_TOKEN``.

Author: Sanju
Date: 2026-08-06
"""
from __future__ import annotations

import argparse
import json
import os
import sys

import httpx
from dotenv import load_dotenv

# Load backend/.env then repo root .env
_HERE = os.path.dirname(os.path.abspath(__file__))
_BACKEND = os.path.dirname(_HERE)
_ROOT = os.path.dirname(_BACKEND)
load_dotenv(os.path.join(_BACKEND, ".env"))
load_dotenv(os.path.join(_ROOT, ".env"))


def main() -> int:
    """
    Purpose:
        Parse CLI flags, POST ``/api/admin/embed-sites``, print JSON + HTML snippet.

    Receives (CLI):
        --name (str, required): Friendly site name.
        --domain (str, required): Hostname to authorize.
        --allow-subdomains (flag): Allow ``*.domain``.
        --allowed-ip (str, repeatable): Optional IP allowlist entries.
        --api-base (str): API origin (default ``http://localhost:8000``).
        --admin-token (str): Admin header token (or env ``ADMIN_TOKEN``).

    Returns:
        int: Process exit code — ``0`` on success, ``1`` on HTTP/network error.

    Side effects:
        Prints EmbedSiteOut JSON and the ``snippet`` string to stdout.
    """
    parser = argparse.ArgumentParser(
        description="Register a domain for the AiCV embed widget and print the snippet."
    )
    parser.add_argument("--name", required=True, help="Friendly name for the site")
    parser.add_argument(
        "--domain",
        required=True,
        help="Hostname only, e.g. example.com or localhost",
    )
    parser.add_argument(
        "--allow-subdomains",
        action="store_true",
        help="Also allow *.domain",
    )
    parser.add_argument(
        "--allowed-ip",
        action="append",
        default=[],
        help="Optional client IP allowlist (repeatable)",
    )
    parser.add_argument(
        "--api-base",
        default=os.getenv("API_BASE_URL", "http://localhost:8000"),
        help="API base URL (default http://localhost:8000)",
    )
    parser.add_argument(
        "--admin-token",
        default=os.getenv("ADMIN_TOKEN", "change-me"),
        help="Admin token (or set ADMIN_TOKEN)",
    )
    args = parser.parse_args()

    payload = {
        "name": args.name,
        "domain": args.domain,
        "allow_subdomains": bool(args.allow_subdomains),
        "allowed_ips": args.allowed_ip or [],
    }
    url = args.api_base.rstrip("/") + "/api/admin/embed-sites"
    headers = {"X-Admin-Token": args.admin_token, "Content-Type": "application/json"}

    try:
        with httpx.Client(timeout=30.0) as client:
            resp = client.post(url, headers=headers, json=payload)
    except Exception as e:
        print(f"Request failed: {e}", file=sys.stderr)
        return 1

    if resp.status_code >= 400:
        print(f"Error {resp.status_code}: {resp.text}", file=sys.stderr)
        return 1

    data = resp.json()
    print(json.dumps(data, indent=2))
    print()
    print("Paste this before </body>:")
    print(data.get("snippet") or "(no snippet — check API base URL)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
