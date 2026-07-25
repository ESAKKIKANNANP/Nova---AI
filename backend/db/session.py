# =============================================================================
# backend/db/session.py
#
# Core database connection and session management.
# Supports both sync (for scripts/migrations) and async (for FastAPI routes).
# =============================================================================

from typing import AsyncGenerator, Generator

from sqlalchemy import create_engine, event
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import get_settings

settings = get_settings()

# -----------------------------------------------------------------------------
# Determine if we are using SQLite (needs special handling)
# -----------------------------------------------------------------------------
_is_sqlite = settings.database_url.startswith("sqlite")

_sync_connect_args = {"check_same_thread": False} if _is_sqlite else {}
_async_connect_args = {"check_same_thread": False} if _is_sqlite else {}

# -----------------------------------------------------------------------------
# Asynchronous Database Connection (FastAPI Layer)
# -----------------------------------------------------------------------------
async_engine = create_async_engine(
    settings.async_database_url,
    pool_pre_ping=not _is_sqlite,
    future=True,
    connect_args=_async_connect_args,
)

async_session_factory = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency provider that yields a new asynchronous database session.
    Automatically handles commit/rollback and closes the session.
    """
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# -----------------------------------------------------------------------------
# Synchronous Database Connection (Alembic & Scripts)
# -----------------------------------------------------------------------------
sync_engine = create_engine(
    settings.database_url,
    pool_pre_ping=not _is_sqlite,
    future=True,
    connect_args=_sync_connect_args,
)

# Enable WAL mode for SQLite for better concurrent read performance
if _is_sqlite:
    @event.listens_for(sync_engine, "connect")
    def _set_sqlite_pragma(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.close()

sync_session_factory = sessionmaker(
    bind=sync_engine,
    class_=Session,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


def get_sync_db() -> Generator[Session, None, None]:
    """
    Yields a new synchronous database session.
    Automatically handles commit/rollback and closes the session.
    """
    session = sync_session_factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
