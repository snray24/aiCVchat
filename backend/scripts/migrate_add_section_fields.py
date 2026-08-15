"""Database migration to add candidate_id, current_designation, and section_type fields."""
import asyncio
from sqlalchemy import text
from app.db.session import engine
from app.core.logging import logger


async def migrate():
    """Add new columns to existing tables."""
    async with engine.begin() as conn:
        # Add candidate_id and current_designation to resumes table
        try:
            await conn.execute(text(
                "ALTER TABLE resumes ADD COLUMN IF NOT EXISTS candidate_id VARCHAR(9)"
            ))
            await conn.execute(text(
                "ALTER TABLE resumes ADD COLUMN IF NOT EXISTS current_designation VARCHAR(255)"
            ))
            await conn.execute(text(
                "CREATE INDEX IF NOT EXISTS ix_resumes_candidate_id ON resumes(candidate_id)"
            ))
            logger.info("Added candidate_id and current_designation to resumes table")
        except Exception as e:
            logger.warning(f"Columns may already exist: {e}")
        
        # Add candidate_id and section_type to resume_chunks table
        try:
            await conn.execute(text(
                "ALTER TABLE resume_chunks ADD COLUMN IF NOT EXISTS candidate_id VARCHAR(9)"
            ))
            await conn.execute(text(
                "ALTER TABLE resume_chunks ADD COLUMN IF NOT EXISTS section_type VARCHAR(50)"
            ))
            await conn.execute(text(
                "CREATE INDEX IF NOT EXISTS ix_resume_chunks_candidate_id ON resume_chunks(candidate_id)"
            ))
            logger.info("Added candidate_id and section_type to resume_chunks table")
        except Exception as e:
            logger.warning(f"Columns may already exist: {e}")
        
        # Create enum type for section_type if it doesn't exist
        try:
            await conn.execute(text(
                "CREATE TYPE sectiontype_enum AS ENUM ('about_me', 'work_experience', 'education', 'certifications', 'achievements', 'skills', 'interest', 'personal_profile')"
            ))
            logger.info("Created sectiontype_enum")
        except Exception as e:
            logger.warning(f"Enum type may already exist: {e}")
        
        logger.info("Migration completed successfully")


if __name__ == "__main__":
    asyncio.run(migrate())
