"""Chat API endpoint."""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.retrieval_service import retrieval_service
from app.services.llm_service import llm_service
from app.core.logging import logger

router = APIRouter()


@router.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, db: AsyncSession = Depends(get_db)):
    """Chat endpoint for resume search and Q&A."""
    try:
        # Search for matching resumes
        matches = await retrieval_service.search(
            query=request.message,
            db=db,
            filters=request.filters
        )
        
        if not matches:
            return ChatResponse(
                answer="No matching resumes found in the database.",
                matches=[],
                email_required=True
            )
        
        # Get context for LLM
        resume_ids = [m.resume_id for m in matches]
        context = await retrieval_service.get_context_for_resumes(resume_ids, db)
        
        # Generate answer
        answer = await llm_service.generate_answer(
            query=request.message,
            context=context,
            history=request.history
        )
        
        return ChatResponse(
            answer=answer,
            matches=matches,
            email_required=True
        )
        
    except Exception as e:
        logger.error(f"Chat error: {e}")
        return ChatResponse(
            answer="I encountered an error processing your request. Please try again.",
            matches=[],
            email_required=True
        )
