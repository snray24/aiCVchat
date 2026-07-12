"""Script to delete all ingested resumes from database and filesystem."""
import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import delete
from app.db.session import AsyncSessionLocal
from app.models.resume import Resume
from app.models.resume_chunk import ResumeChunk
from app.core.config import settings
from app.core.logging import logger


async def delete_all_resumes():
    """Delete all resumes from database and filesystem."""
    
    # Delete from database
    async with AsyncSessionLocal() as db:
        try:
            # Delete all chunks first
            await db.execute(delete(ResumeChunk))
            logger.info("Deleted all resume chunks from database")
            
            # Delete all resumes
            await db.execute(delete(Resume))
            logger.info("Deleted all resumes from database")
            
            await db.commit()
            print("✓ Database cleared: all resumes and chunks deleted")
        except Exception as e:
            logger.error(f"Database deletion error: {e}")
            await db.rollback()
            print(f"✗ Database error: {e}")
            return False
    
    # Delete from filesystem
    try:
        resume_dir = Path(settings.resume_data_dir)
        if resume_dir.exists():
            deleted_files = []
            for file_path in resume_dir.glob("*"):
                if file_path.is_file() and file_path.name != ".gitkeep":
                    file_path.unlink()
                    deleted_files.append(file_path.name)
            
            if deleted_files:
                logger.info(f"Deleted resume files: {deleted_files}")
                print(f"✓ Filesystem cleared: {len(deleted_files)} resume file(s) deleted")
            else:
                print("✓ Filesystem: no resume files to delete")
        else:
            print(f"✓ Filesystem: directory does not exist ({resume_dir})")
        
        return True
    except Exception as e:
        logger.error(f"Filesystem deletion error: {e}")
        print(f"✗ Filesystem error: {e}")
        return False


if __name__ == "__main__":
    success = asyncio.run(delete_all_resumes())
    if success:
        print("\n✓ All resumes deleted successfully")
        sys.exit(0)
    else:
        print("\n✗ Failed to delete all resumes")
        sys.exit(1)
