"""Chat API endpoint."""
import re
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.retrieval_service import retrieval_service
from app.services.llm_service import llm_service
from app.core.logging import logger
from app.api.deps import require_embed_session

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


@router.post("/api/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db),
    _session: dict = Depends(require_embed_session),
):
    """Chat endpoint for resume search and Q&A."""
    try:
        matches = await retrieval_service.search(
            query=request.message,
            db=db,
            filters=request.filters,
        )

        if not matches:
            return ChatResponse(
                answer="No matching resumes found in the database.",
                matches=[],
                email_required=True,
            )

        if is_requesting_resumes(request.message):
            return ChatResponse(
                answer=(
                    f"I found {len(matches)} matching resume(s). To receive them via email, "
                    "please provide your email address. I can only send resumes to registered users."
                ),
                matches=matches,
                email_required=True,
            )

        resume_ids = [m.resume_id for m in matches]
        context = await retrieval_service.get_context_for_resumes(resume_ids, db)

        answer = await llm_service.generate_answer(
            query=request.message,
            context=context,
            history=request.history,
        )

        return ChatResponse(
            answer=answer,
            matches=matches,
            email_required=True,
        )

    except Exception as e:
        logger.error(f"Chat error: {e}")
        return ChatResponse(
            answer="I encountered an error processing your request. Please try again.",
            matches=[],
            email_required=True,
        )
