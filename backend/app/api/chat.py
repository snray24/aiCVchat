"""Chat API endpoint."""
import re
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.db.session import get_db
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.retrieval_service import retrieval_service
from app.services.llm_service import llm_service
from app.core.logging import logger
from app.models.resume import Resume

router = APIRouter()


def is_requesting_resumes(message: str) -> bool:
    """Detect if user is requesting to send/share resumes."""
    lower_msg = message.lower()
    patterns = [
        r'\b(send|share|request|mail|email|forward|transmit|provide).*\b(resume|resumes|cv|profile|document)\b',
        r'\b(send|share|request|mail|email|forward|transmit|provide).*\b(their|me|them|us)\b',
        r'\b(resume|resumes|cv).*\b(send|share|mail|email)\b',
    ]
    return any(re.search(pattern, lower_msg) for pattern in patterns)


def is_asking_total_count(message: str) -> bool:
    """Detect if the user is asking for the total number of indexed resumes/candidates."""
    lower_msg = message.lower()
    patterns = [
        r"\bhow many (candidates|resumes|profiles|people)\b",
        r"\btotal (candidates|resumes|profiles)\b",
        r"\bnumber of (candidates|resumes|profiles)\b",
        r"\bhow many do you have\b",
    ]
    return any(re.search(p, lower_msg) for p in patterns)


@router.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, db: AsyncSession = Depends(get_db)):
    """Chat endpoint for resume search and Q&A."""
    try:
        # If user asks for total inventory, return DB count instead of search-topk
        if is_asking_total_count(request.message):
            result = await db.execute(select(func.count()).select_from(Resume))
            total = result.scalar_one()
            return ChatResponse(
                answer=f"We currently have {total} indexed resume(s).",
                matches=[],
                email_required=False
            )

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
        
        # Check if user is requesting resumes - if so, ask for email instead of generating answer
        if is_requesting_resumes(request.message):
            return ChatResponse(
                answer=f"I found {len(matches)} matching resume(s). To receive them via email, please provide your email address. I can only send resumes to registered users.",
                matches=matches,
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
