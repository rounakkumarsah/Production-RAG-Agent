"""
PostgreSQL async engine & session factory.

We use SQLAlchemy 2.x with asyncpg driver.
The engine is created once and reused for the application lifetime.
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.config import get_settings
from app.utils.logging import get_logger

logger = get_logger(__name__)

_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


class Base(DeclarativeBase):
    """Base class for all ORM models."""


def get_engine() -> AsyncEngine:
    global _engine
    if _engine is None:
        settings = get_settings()
        _engine = create_async_engine(
            settings.postgres_dsn,
            pool_pre_ping=True,       # detect stale connections
            pool_size=10,
            max_overflow=20,
            echo=settings.DEBUG,
        )
        logger.info("PostgreSQL engine created — host=%s db=%s",
                    settings.POSTGRES_HOST, settings.POSTGRES_DB)
    return _engine


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    global _session_factory
    if _session_factory is None:
        _session_factory = async_sessionmaker(
            bind=get_engine(),
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
        )
    return _session_factory


@asynccontextmanager
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Async context manager that yields a session and handles commit/rollback.
    Usage:
        async with get_db_session() as session:
            ...
    """
    factory = get_session_factory()
    async with factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def dispose_engine() -> None:
    """Gracefully close the connection pool on shutdown."""
    global _engine
    if _engine is not None:
        await _engine.dispose()
        logger.info("PostgreSQL engine disposed")
        _engine = None
