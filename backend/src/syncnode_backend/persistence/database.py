"""
SyncNode — database engine and session factory.

Provides:
  - Async SQLAlchemy engine
  - Session factory
  - Database initialization (create_all for dev, alembic for prod)
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from syncnode_backend.config.settings import settings
from syncnode_backend.persistence.models import Base

_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def get_engine() -> AsyncEngine:
    """Return (or create) the shared async engine."""
    global _engine
    if _engine is None:
        connect_args = {}
        if "sqlite" in settings.database_url:
            connect_args["check_same_thread"] = False

        if "sqlite" in settings.database_url:
            # SQLite has a single writer. WAL + a busy timeout let concurrent
            # async writers (parallel LangGraph branches) serialize gracefully
            # instead of raising "database is locked".
            connect_args["timeout"] = 30
        _engine = create_async_engine(
            settings.database_url,
            echo=settings.syncnode_debug,
            connect_args=connect_args,
        )
        if "sqlite" in settings.database_url:
            from sqlalchemy import event

            @event.listens_for(_engine.sync_engine, "connect")
            def _set_sqlite_pragma(dbapi_conn, _rec):  # noqa: ANN001
                cur = dbapi_conn.cursor()
                cur.execute("PRAGMA journal_mode=WAL")
                cur.execute("PRAGMA busy_timeout=30000")
                cur.execute("PRAGMA synchronous=NORMAL")
                cur.close()
    return _engine


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    """Return (or create) the shared session factory."""
    global _session_factory
    if _session_factory is None:
        _session_factory = async_sessionmaker(
            bind=get_engine(),
            expire_on_commit=False,
            autoflush=False,
            autocommit=False,
        )
    return _session_factory


@asynccontextmanager
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Async context manager that yields a database session."""
    factory = get_session_factory()
    async with factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def init_database() -> None:
    """Create all tables (development only — use alembic for production)."""
    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_database() -> None:
    """Dispose the engine on shutdown."""
    global _engine
    if _engine is not None:
        await _engine.dispose()
        _engine = None
