"""Resume request API endpoint."""
from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pathlib import Path
from app.db.session import get_db
from app.schemas.request_resume import RequestResumeRequest, RequestResumeResponse
from app.models.resume import Resume
from app.models.resume_request import ResumeRequest
from app.models.audit_log import AllowedEmailAuditLog
from app.services.allowlist_service import allowlist_service
from app.services.email_service import email_service
from app.core.config import settings
from app.core.logging import logger

router = APIRouter()


@router.post("/api/request-resumes", response_model=RequestResumeResponse)
async def request_resumes(
    request: RequestResumeRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """Request resumes by email with allowlist validation."""
    normalized_email = request.email.strip().lower()
    
    # Check allowlist
    is_allowed = allowlist_service.is_email_allowed(normalized_email)
    
    # Log audit entry
    audit_log = AllowedEmailAuditLog(
        email_entered=normalized_email,
        matched=is_allowed,
        action="resume_request"
    )
    db.add(audit_log)
    
    if not is_allowed:
        await db.commit()
        return RequestResumeResponse(
            status="denied",
            message="Your email is not authorized to receive resumes."
        )
    
    # Get resume details
    result = await db.execute(
        select(Resume).where(Resume.id.in_(request.resume_ids))
    )
    resumes = result.scalars().all()
    
    if not resumes:
        await db.commit()
        return RequestResumeResponse(
            status="denied",
            message="No valid resumes found."
        )
    
    # Check limit
    if len(resumes) > settings.max_resumes_per_request:
        await db.commit()
        return RequestResumeResponse(
            status="denied",
            message=f"Maximum {settings.max_resumes_per_request} resumes per request."
        )
    
    # Create request record
    resume_request = ResumeRequest(
        requester_email=normalized_email,
        requested_resume_ids=request.resume_ids,
        status="accepted",
        message="Email queued for sending"
    )
    db.add(resume_request)
    await db.commit()
    
    # Queue email sending in background
    if email_service.is_configured():
        resume_files = [Path(r.source_file_path) for r in resumes]
        background_tasks.add_task(
            email_service.send_resumes,
            to_email=request.email,
            resume_files=resume_files
        )
    else:
        logger.warning("SMTP not configured, skipping email send")
        resume_request.status = "failed"
        resume_request.message = "SMTP not configured"
        await db.commit()
    
    return RequestResumeResponse(
        status="accepted",
        message="Resumes will be sent to your email shortly."
    )
