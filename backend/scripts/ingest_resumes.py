"""Script to trigger resume ingestion via API.

This script is a small helper used in development to call the admin
ingest endpoint. Improve error handling so we don't show spurious
exceptions when the server actually performed the ingestion but
returned unexpected or non-JSON content.
"""
import httpx
import sys
import json
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.config import settings


async def ingest_resumes():
    """Trigger resume ingestion via admin API."""
    url = f"http://{settings.api_host}:{settings.api_port}/api/admin/ingest"
    headers = {"X-Admin-Token": settings.admin_token}

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, headers=headers)
            # Raise for non-2xx status codes
            response.raise_for_status()

            # Try to parse JSON response; fall back to raw text if parsing fails
            try:
                body = response.json()
            except Exception:
                text = response.text
                print("Ingestion triggered (non-JSON response):")
                print(text)
                return

            # Log structured result
            print("Ingestion triggered successfully")
            print(json.dumps(body, indent=2))

        except httpx.HTTPStatusError as e:
            # Server returned an error status (4xx/5xx)
            text = e.response.text if e.response is not None else str(e)
            print(f"Ingestion request failed with status {e.response.status_code if e.response is not None else 'N/A'}: {text}")
            sys.exit(1)
        except httpx.HTTPError as e:
            # Network or client error
            print(f"HTTP error triggering ingestion: {e}")
            print(f"Error type: {type(e).__name__}")
            import traceback
            traceback.print_exc()
            sys.exit(1)
        except Exception as e:
            # Unexpected error in the client script
            print(f"Unexpected error: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)


if __name__ == "__main__":
    import asyncio
    asyncio.run(ingest_resumes())
