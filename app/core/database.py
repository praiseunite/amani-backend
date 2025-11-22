"""
Database configuration with async SQLAlchemy and PostgreSQL (Supabase).
"""

from typing import AsyncGenerator, Optional

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import declarative_base

from app.core.config import settings

# Base class for models (must be defined first)
Base = declarative_base()

# Create async engine only if using async driver
# This allows alembic migrations to work with psycopg2
engine: Optional[AsyncEngine] = None
AsyncSessionLocal: Optional[async_sessionmaker] = None

if settings.DATABASE_URL and settings.DATABASE_URL.startswith("postgresql+asyncpg://"):
    engine = create_async_engine(
        settings.DATABASE_URL,
        echo=settings.DEBUG,
        future=True,
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20,
    )

    # Create async session factory
    AsyncSessionLocal = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False, autocommit=False, autoflush=False
    )


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency for getting async database sessions.

    Yields:
        AsyncSession: Database session

    Raises:
        RuntimeError: If async engine is not initialized (e.g., using psycopg2 instead of asyncpg)
    """
    if AsyncSessionLocal is None:
        raise RuntimeError(
            "AsyncSessionLocal is not initialized. "
            "Ensure DATABASE_URL uses asyncpg driver (postgresql+asyncpg://...)"
        )

    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    """
    Initialize database tables.
    Should be called on application startup.

    Raises:
        RuntimeError: If async engine is not initialized (e.g., using psycopg2 instead of asyncpg)
    """
    if engine is None:
        raise RuntimeError(
            "Async engine is not initialized. "
            "Ensure DATABASE_URL uses asyncpg driver (postgresql+asyncpg://...)"
        )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
