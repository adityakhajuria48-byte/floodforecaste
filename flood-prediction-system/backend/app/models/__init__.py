"""
Database connection and session management
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator

from app.core.config import settings
from app.models.database import Base


# Sync engine for migrations and sync operations
sync_engine = create_engine(
    settings.database_url,
    echo=settings.DEBUG,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)

# Async engine for async operations
async_engine = create_async_engine(
    settings.async_database_url,
    echo=settings.DEBUG,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)

# Session factories
SyncSessionLocal = sessionmaker(bind=sync_engine, autocommit=False, autoflush=False)
AsyncSessionLocal = sessionmaker(bind=async_engine, class_=AsyncSession, expire_on_commit=False)


def get_db() -> Generator[Session, None, None]:
    """Dependency for getting database session"""
    db = SyncSessionLocal()
    try:
        yield db
    finally:
        db.close()


async def get_async_db() -> Generator[AsyncSession, None, None]:
    """Dependency for getting async database session"""
    db = AsyncSessionLocal()
    try:
        yield db
    finally:
        await db.close()


def init_db():
    """Initialize database tables"""
    Base.metadata.create_all(bind=sync_engine)


def drop_db():
    """Drop all tables (use with caution)"""
    Base.metadata.drop_all(bind=sync_engine)
