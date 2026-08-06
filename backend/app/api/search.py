"""Search API endpoint."""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.schemas.search import SearchRequest, SearchResponse
from app.services.retrieval_service import retrieval_service
from app.core.logging import logger
from app.api.deps import require_embed_session

router = APIRouter()


@router.post("/api/search", response_model=SearchResponse)
async def search(
    request: SearchRequest,
    db: AsyncSession = Depends(get_db),
    _session: dict = Depends(require_embed_session),
):
    """Search endpoint for resume shortlisting without chat."""
    try:
        matches = await retrieval_service.search(
            query=request.query,
            db=db,
            filters=request.filters,
        )

        return SearchResponse(
            matches=matches,
            total=len(matches),
        )

    except Exception as e:
        logger.error(f"Search error: {e}")
        return SearchResponse(
            matches=[],
            total=0,
        )
