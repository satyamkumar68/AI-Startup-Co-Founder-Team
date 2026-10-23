from typing import AsyncGenerator, Optional
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from backend.app.core.config import settings
from backend.app.models.db import Base


# Async database engine & session (for FastAPI & async operations)
async_engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    future=True,
    pool_pre_ping=True
)

AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)


# Synchronous engine & session (for Celery/RQ workers, Alembic, or migrations)
sync_engine = create_engine(
    settings.DATABASE_SYNC_URL,
    echo=False,
    pool_pre_ping=True
)

SyncSessionLocal = sessionmaker(
    bind=sync_engine,
    autocommit=False,
    autoflush=False,
    class_=Session
)


async def get_async_db() -> AsyncGenerator[Optional[AsyncSession], None]:
    """Dependency for obtaining an asynchronous database session with safe fallback."""
    session = None
    try:
        session = AsyncSessionLocal()
    except Exception:
        # Fall back gracefully to None if DB engine initialization fails
        yield None
        return

    try:
        yield session
    finally:
        await session.close()


def get_sync_db() -> Session:
    """Helper to obtain a synchronous database session."""
    db = SyncSessionLocal()
    try:
        return db
    finally:
        db.close()


async def init_db() -> None:
    """Create all tables asynchronously (used for local setup or testing)."""
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
