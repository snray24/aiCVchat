"""Optional script to seed sample resume data for testing."""
import asyncio
from pathlib import Path
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import AsyncSessionLocal, engine
from app.db.init_db import init_database
from app.core.logging import logger


async def main():
    """Initialize database and seed sample data."""
    # Initialize database
    await init_database()
    logger.info("Database initialized")
    
    # Create sample data directory
    resume_dir = Path("backend/data/resumes")
    resume_dir.mkdir(parents=True, exist_ok=True)
    
    # Create a sample plaintext email list for encryption
    allowed_emails_path = Path("backend/data/allowed_emails.txt")
    if not allowed_emails_path.exists():
        allowed_emails_path.write_text(
            "admin@example.com\n"
            "hr@company.com\n"
            "recruiter@company.com\n"
        )
        print(f"Created sample email list at {allowed_emails_path}")
        print("Run: python scripts/encrypt_allowlist.py --input backend/data/allowed_emails.txt")
    
    print("Setup complete. Place resume PDF/DOCX files in backend/data/resumes/")
    print("Then run: python scripts/ingest_resumes.py")


if __name__ == "__main__":
    asyncio.run(main())
