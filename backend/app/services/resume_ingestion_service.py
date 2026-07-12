"""Resume ingestion service for processing and storing resumes."""
import asyncio
from pathlib import Path
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete, select, text
from app.models.resume import Resume
from app.models.resume_chunk import ResumeChunk
from app.services.resume_parser import resume_parser
from app.services.chunking_service import chunking_service
from app.services.embedding_service import embedding_service
from app.services.llm_service import llm_service
from app.core.config import settings
from app.core.logging import logger


class ResumeIngestionService:
    """Service for ingesting resumes into the database."""
    
    def __init__(self):
        self.parser = resume_parser
        self.chunker = chunking_service
        self.embedder = embedding_service
        self.llm = llm_service
        self.resume_dir = Path(settings.resume_data_dir)
    
    async def ingest_file(self, file_path: Path, db: AsyncSession) -> Resume | None:
        """Ingest a single resume file."""
        try:
            # Check file type
            if file_path.suffix.lower() not in self.parser.SUPPORTED_EXTENSIONS:
                logger.warning(f"Skipping unsupported file: {file_path}")
                return None
            
            # Compute file hash
            file_hash = self.parser.compute_file_hash(file_path)
            
            # Check if already ingested
            existing_resume = (
                await db.execute(
                    select(Resume).where(Resume.file_hash == file_hash)
                )
            ).scalar_one_or_none()
            if existing_resume:
                existing_chunks = (
                    await db.execute(
                        select(ResumeChunk).where(ResumeChunk.resume_id == existing_resume.id)
                    )
                ).scalars().all()
                if existing_chunks:
                    logger.info(f"Resume already ingested (hash match): {file_path.name}")
                    return None

                logger.info(f"Resume exists without embeddings; reprocessing: {file_path.name}")
            
            # Extract text
            text = self.parser.extract_text(file_path)
            if not text:
                logger.warning(f"No text extracted from: {file_path}")
                return None
            
            # Extract metadata using LLM
            metadata = await self.llm.extract_metadata(text)
            
            # Create or refresh resume record
            resume = existing_resume or Resume(
                full_name=metadata.get("full_name") or file_path.stem,
                current_title=metadata.get("current_title"),
                total_years_experience=metadata.get("total_years_experience"),
                summary=metadata.get("summary"),
                skills_text=metadata.get("skills"),
                education_text=metadata.get("education"),
                certifications_text=metadata.get("certifications"),
                last_company=metadata.get("last_company"),
                location=metadata.get("location"),
                source_file_name=file_path.name,
                source_file_path=str(file_path),
                extracted_text=text,
                file_hash=file_hash
            )
            if existing_resume:
                resume.full_name = metadata.get("full_name") or file_path.stem
                resume.current_title = metadata.get("current_title")
                resume.total_years_experience = metadata.get("total_years_experience")
                resume.summary = metadata.get("summary")
                resume.skills_text = metadata.get("skills")
                resume.education_text = metadata.get("education")
                resume.certifications_text = metadata.get("certifications")
                resume.last_company = metadata.get("last_company")
                resume.location = metadata.get("location")
                resume.source_file_name = file_path.name
                resume.source_file_path = str(file_path)
                resume.extracted_text = text
                resume.file_hash = file_hash
            else:
                db.add(resume)
            
            await db.flush()
            await db.execute(delete(ResumeChunk).where(ResumeChunk.resume_id == resume.id))
            
            # Chunk and embed
            chunks = self.chunker.chunk_with_metadata(text, {
                "resume_id": str(resume.id),
                "file_name": file_path.name
            })
            
            # Generate embeddings for chunks
            chunk_texts = [c["chunk_text"] for c in chunks]
            embeddings = await self.embedder.embed_texts(chunk_texts)
            
            # Store chunks
            for idx, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                resume_chunk = ResumeChunk(
                    resume_id=resume.id,
                    chunk_index=idx,
                    chunk_text=chunk["chunk_text"],
                    embedding=embedding,
                    metadata_json=chunk["metadata"]
                )
                db.add(resume_chunk)
            
            await db.commit()
            logger.info(f"Successfully ingested: {file_path.name}")
            return resume
            
        except Exception as e:
            logger.error(f"Error ingesting {file_path}: {e}")
            await db.rollback()
            return None
    
    async def ingest_directory(self, db: AsyncSession) -> dict:
        """Ingest all resume files from the configured directory."""
        logger.info(f"Looking for resumes in: {self.resume_dir}")
        logger.info(f"Absolute path: {self.resume_dir.absolute()}")
        logger.info(f"Directory exists: {self.resume_dir.exists()}")
        
        if not self.resume_dir.exists():
            logger.warning(f"Resume directory does not exist: {self.resume_dir}")
            return {"total": 0, "ingested": 0, "skipped": 0, "errors": 0}
        
        files = list(self.resume_dir.glob("*"))
        logger.info(f"Found {len(files)} files in directory")
        resume_files = [f for f in files if f.is_file() and f.suffix.lower() in self.parser.SUPPORTED_EXTENSIONS]
        logger.info(f"Filtered to {len(resume_files)} resume files: {[f.name for f in resume_files]}")
        
        results = {"total": len(resume_files), "ingested": 0, "skipped": 0, "errors": 0}
        
        for file_path in resume_files:
            logger.info(f"Processing file: {file_path}")
            result = await self.ingest_file(file_path, db)
            if result:
                results["ingested"] += 1
            else:
                results["skipped"] += 1
        
        logger.info(f"Ingestion complete: {results}")
        return results
    
    async def reindex_all(self, db: AsyncSession) -> dict:
        """Delete all existing resumes and re-ingest from directory."""
        # Delete all chunks and resumes using ORM delete
        await db.execute(delete(ResumeChunk))
        await db.execute(delete(Resume))
        await db.commit()
        
        logger.info("Cleared existing resumes, re-indexing...")
        return await self.ingest_directory(db)


resume_ingestion_service = ResumeIngestionService()
