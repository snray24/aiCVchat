"""Database session management."""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from app.core.config import settings
from app.core.logging import logger

# Create async engine
engine = create_async_engine(
    settings.database_url,
    echo=settings.app_env == "development",
    future=True,
    # Fail fast when PostgreSQL is down (default TCP hang blocks uvicorn startup)
    connect_args={"connect_timeout": 5},
    pool_pre_ping=True,
)


# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)


async def get_db() -> AsyncSession:
    """Dependency for getting async database sessions."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
