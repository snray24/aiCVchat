"""Admin API endpoint for ingestion."""
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.services.resume_ingestion_service import resume_ingestion_service
from app.core.config import settings
from app.core.logging import logger

router = APIRouter()


async def verify_admin_token(x_admin_token: str = Header(None)):
    """Verify admin token for protected endpoints."""
    if x_admin_token != settings.admin_token:
        raise HTTPException(status_code=403, detail="Invalid admin token")
    return True


@router.post("/api/admin/ingest")
async def trigger_ingestion(
    admin_verified: bool = Depends(verify_admin_token),
    db: AsyncSession = Depends(get_db)
):
    """Trigger resume ingestion from local directory."""
    try:
        results = await resume_ingestion_service.ingest_directory(db)
        return {
            "status": "success",
            "results": results
        }
    except Exception as e:
        logger.error(f"Ingestion error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/admin/reindex")
async def trigger_reindex(
    admin_verified: bool = Depends(verify_admin_token),
    db: AsyncSession = Depends(get_db)
):
    """Trigger full re-index (delete and re-ingest all resumes)."""
    try:
        results = await resume_ingestion_service.reindex_all(db)
        return {
            "status": "success",
            "results": results
        }
    except Exception as e:
        logger.error(f"Reindex error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
