"""Script to trigger resume ingestion via API."""
import httpx
import sys
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
            response.raise_for_status()
            print("Ingestion triggered successfully")
            print(response.json())
        except httpx.HTTPError as e:
            print(f"Error triggering ingestion: {e}")
            sys.exit(1)


if __name__ == "__main__":
    import asyncio
    asyncio.run(ingest_resumes())
