"""Retrieval service for semantic search and candidate matching."""
from typing import List, Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func
from pgvector.sqlalchemy import Vector
from app.models.resume import Resume
from app.models.resume_chunk import ResumeChunk
from app.services.embedding_service import embedding_service
from app.core.config import settings
from app.core.logging import logger
from app.schemas.chat import ChatFilters, CandidateMatch


class RetrievalService:
    """Service for retrieving and ranking resumes."""
    
    def __init__(self):
        self.embedder = embedding_service
        self.top_k = settings.top_k_chunks
    
    async def search(
        self,
        query: str,
        db: AsyncSession,
        filters: Optional[ChatFilters] = None
    ) -> List[CandidateMatch]:
        """Perform semantic search with optional metadata filters."""
        # Generate query embedding
        query_embedding = await self.embedder.embed_text(query)
        if not query_embedding:
            return []
        
        # Build base query with vector similarity
        base_query = select(
            ResumeChunk,
            Resume,
            (1 - ResumeChunk.embedding.cosine_distance(query_embedding)).label("similarity")
        ).join(Resume, ResumeChunk.resume_id == Resume.id)
        
        # Apply metadata filters
        if filters:
            conditions = []
            
            if filters.skills:
                conditions.append(Resume.skills_text.ilike(f"%{filters.skills}%"))
            
            if filters.min_years_experience is not None:
                conditions.append(
                    (Resume.total_years_experience >= filters.min_years_experience) |
                    (Resume.total_years_experience.is_(None))
                )
            
            if filters.current_title:
                conditions.append(Resume.current_title.ilike(f"%{filters.current_title}%"))
            
            if filters.education:
                conditions.append(Resume.education_text.ilike(f"%{filters.education}%"))
            
            if filters.location:
                conditions.append(Resume.location.ilike(f"%{filters.location}%"))
            
            if conditions:
                base_query = base_query.where(and_(*conditions))
        
        # Order by similarity and limit
        base_query = base_query.order_by(
            (1 - ResumeChunk.embedding.cosine_distance(query_embedding)).desc()
        ).limit(self.top_k * 2)  # Get more to group by resume
        
        # Execute query
        result = await db.execute(base_query)
        rows = result.all()
        
        # Group by resume and score
        resume_scores: Dict[str, float] = {}
        resume_chunks: Dict[str, List[str]] = {}
        
        for chunk, resume, similarity in rows:
            resume_id = str(resume.id)
            if resume_id not in resume_scores:
                resume_scores[resume_id] = similarity
                resume_chunks[resume_id] = []
            else:
                resume_scores[resume_id] = max(resume_scores[resume_id], similarity)
            resume_chunks[resume_id].append(chunk.chunk_text)
        
        # Get full resume details for matched resumes
        resume_ids = list(resume_scores.keys())
        resumes_result = await db.execute(
            select(Resume).where(Resume.id.in_(resume_ids))
        )
        resumes = {str(r.id): r for r in resumes_result.scalars().all()}
        
        # Build candidate matches with scoring
        matches = []
        for resume_id, score in resume_scores.items():
            resume = resumes.get(resume_id)
            if not resume:
                continue
            
            # Extract top skills
            skills = []
            if resume.skills_text:
                skills = [s.strip() for s in resume.skills_text.split(",")][:5]
            
            # Generate match reason
            match_reason = self._generate_match_reason(resume, score, filters)
            
            match = CandidateMatch(
                resume_id=resume_id,
                full_name=resume.full_name,
                current_title=resume.current_title,
                years_experience=resume.total_years_experience,
                top_skills=skills,
                short_match_reason=match_reason
            )
            matches.append(match)
        
        # Sort by score
        matches.sort(key=lambda x: resume_scores[x.resume_id], reverse=True)
        
        return matches[:self.top_k]
    
    async def get_context_for_resumes(
        self,
        resume_ids: List[str],
        db: AsyncSession
    ) -> str:
        """Get concatenated context from resume chunks for given resume IDs."""
        if not resume_ids:
            return ""
        
        result = await db.execute(
            select(ResumeChunk, Resume)
            .join(Resume, ResumeChunk.resume_id == Resume.id)
            .where(Resume.id.in_(resume_ids))
            .order_by(ResumeChunk.chunk_index)
        )
        
        context_parts = []
        current_resume_id = None
        
        for chunk, resume in result.all():
            if str(resume.id) != current_resume_id:
                context_parts.append(f"\n--- Resume: {resume.full_name} ({resume.current_title or 'N/A'}) ---")
                current_resume_id = str(resume.id)
            context_parts.append(chunk.chunk_text)
        
        return "\n".join(context_parts)
    
    def _generate_match_reason(
        self,
        resume: Resume,
        similarity: float,
        filters: Optional[ChatFilters]
    ) -> str:
        """Generate a short reason for the match."""
        reasons = []
        
        if resume.current_title:
            reasons.append(f"Role: {resume.current_title}")
        
        if resume.total_years_experience:
            reasons.append(f"{resume.total_years_experience} years experience")
        
        if resume.skills_text:
            top_skills = resume.skills_text.split(",")[:2]
            reasons.append(f"Skills: {', '.join(top_skills)}")
        
        if filters and filters.skills:
            if filters.skills.lower() in (resume.skills_text or "").lower():
                reasons.append("Matches skill filter")
        
        base_reason = "; ".join(reasons) if reasons else "Profile match"
        return f"{base_reason} (score: {similarity:.2f})"


retrieval_service = RetrievalService()
