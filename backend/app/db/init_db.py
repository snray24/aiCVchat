"""Database initialization script."""
import asyncio
from sqlalchemy import text
from app.db.session import engine
from app.db.base import Base
from app.models.resume import Resume
from app.models.resume_chunk import ResumeChunk
from app.models.resume_request import ResumeRequest
from app.models.audit_log import AllowedEmailAuditLog
from app.core.logging import logger


async def init_database():
    """Initialize database with pgvector extension and create tables."""
    async with engine.begin() as conn:
        # Enable pgvector extension
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        logger.info("pgvector extension enabled")
        
        # Create all tables
        await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables created")


async def reset_database():
    """Drop and recreate all tables (use with caution)."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
        logger.info("Database reset complete")


if __name__ == "__main__":
    asyncio.run(init_database())
