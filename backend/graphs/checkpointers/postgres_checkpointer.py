# =============================================================================
# graphs/checkpointers/postgres_checkpointer.py
#
# LangGraph Checkpointer — Autonomous Data Scientist
#
# What is a checkpointer?
# ────────────────────────
# A LangGraph *checkpointer* is a pluggable persistence layer that saves the
# full ``GraphState`` after every node execution.  This enables:
#
#   • **Fault tolerance** — if a Celery worker crashes mid-pipeline, a new
#     worker can resume from the last saved checkpoint rather than restarting.
#   • **Human-in-the-loop** — the graph can pause at ``human_review_node``
#     and be resumed hours later by a different process.
#   • **Replay / debugging** — every intermediate state is stored, so we can
#     step through the execution history in the UI.
#   • **Time-travel** — LangGraph can rewind to any saved checkpoint and
#     re-execute from that point.
#
# Checkpoint backends
# ────────────────────
# LangGraph ships official checkpoint packages that implement the
# ``BaseCheckpointSaver`` interface:
#
#   langgraph-checkpoint-postgres  → stores in PostgreSQL (production)
#   langgraph-checkpoint-redis     → stores in Redis (optional)
#   MemorySaver (built-in)         → in-process dict (tests / dev)
#
# This module provides:
#   1. ``get_checkpointer(settings)`` — factory that returns the right saver.
#   2. ``PostgresCheckpointer`` — thin wrapper around
#      ``langgraph_checkpoint_postgres.PostgresSaver`` with our schema +
#      connection-pool management.
#   3. ``checkpoint_context()`` — async context manager used by
#      ``graph.invoke()`` and ``graph.stream()`` callers.
#
# Schema
# ───────
# The ``langgraph-checkpoint-postgres`` library manages its own DDL.
# We call ``saver.setup()`` once at startup to create the required tables
# (``checkpoints``, ``checkpoint_blobs``, ``checkpoint_writes``) if they
# do not already exist.
# =============================================================================

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING, AsyncGenerator, Any

if TYPE_CHECKING:
    from config import CheckpointerBackend, Settings

log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# In-memory checkpointer (tests / local dev)
# ---------------------------------------------------------------------------

def get_memory_checkpointer() -> Any:
    """
    Return a ``langgraph.checkpoint.memory.MemorySaver`` instance.

    ``MemorySaver`` is the built-in LangGraph checkpointer that stores all
    state in a plain Python dict.  It requires **no external dependencies**
    and is the default for unit tests and local development.

    State is lost when the process exits — do not use in production.

    Returns:
        A ``MemorySaver`` ready to be passed to ``StateGraph.compile()``.
    """
    from langgraph.checkpoint.memory import MemorySaver

    saver = MemorySaver()
    log.info("checkpointer_ready", backend="memory")
    return saver


# ---------------------------------------------------------------------------
# PostgreSQL checkpointer (production)
# ---------------------------------------------------------------------------

class PostgresCheckpointer:
    """
    Wrapper around ``langgraph_checkpoint_postgres.PostgresSaver``.

    Responsibilities
    ─────────────────
    1. **Lazy schema setup** — calls ``saver.setup()`` once at first use
       to create the checkpoint tables if they do not exist.
    2. **Connection pooling** — uses ``psycopg.AsyncConnectionPool``
       (the async driver used by ``PostgresSaver`` under the hood).
    3. **Graceful teardown** — the ``lifespan()`` context manager closes
       the connection pool when the application shuts down.

    Usage (inside FastAPI lifespan)::

        pg_cp = PostgresCheckpointer(settings)
        async with pg_cp.lifespan() as saver:
            compiled = graph.compile(checkpointer=saver)
            # Use compiled graph for the app's lifetime

    Usage (simple, without lifespan context)::

        saver = await pg_cp.get_saver()
        compiled = graph.compile(checkpointer=saver)
    """

    def __init__(self, settings: "Settings") -> None:
        self._db_url = self._build_psycopg_url(settings.async_database_url)
        self._saver: Any = None   # PostgresSaver instance, set in setup()
        self._pool: Any  = None   # psycopg.AsyncConnectionPool

    @staticmethod
    def _build_psycopg_url(async_dsn: str) -> str:
        """
        Convert an ``asyncpg`` DSN to a ``psycopg`` DSN.

        ``langgraph-checkpoint-postgres`` requires the ``psycopg3`` driver
        (``postgresql+psycopg``) while SQLAlchemy uses ``asyncpg`` for its
        own connections.  This method performs the simple string substitution.

        Example::

            "postgresql+asyncpg://user:pass@host/db"
            → "postgresql+psycopg://user:pass@host/db"
        """
        return async_dsn.replace(
            "postgresql+asyncpg", "postgresql+psycopg"
        ).replace(
            "asyncpg://", "postgresql://"
        )

    async def _setup(self) -> Any:
        """
        Create the checkpointer and run schema migrations if necessary.

        This is called once lazily — the first time ``get_saver()`` is
        invoked.  Subsequent calls return the cached instance.

        Returns:
            The initialised ``PostgresSaver`` instance.
        """
        if self._saver is not None:
            return self._saver

        try:
            from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
            import psycopg

            # Build a plain psycopg3 connection URL (strip SQLAlchemy dialect prefix)
            raw_url = self._db_url.replace("postgresql+psycopg://", "postgresql://")

            conn = await psycopg.AsyncConnection.connect(raw_url)
            self._saver = AsyncPostgresSaver(conn)

            # Create checkpoint tables if they don't exist
            await self._saver.setup()

            log.info("postgres_checkpointer_ready", db_url=raw_url[:30] + "...")
        except ImportError as exc:
            raise RuntimeError(
                "langgraph-checkpoint-postgres is not installed. "
                "Run: pip install langgraph-checkpoint-postgres"
            ) from exc
        except Exception as exc:
            log.error("postgres_checkpointer_setup_failed", error=str(exc))
            raise

        return self._saver

    async def get_saver(self) -> Any:
        """
        Return the initialised ``AsyncPostgresSaver``.

        Initialises the saver on first call (lazy setup).

        Returns:
            The ``AsyncPostgresSaver`` ready to be passed to
            ``graph.compile(checkpointer=saver)``.
        """
        return await self._setup()

    @asynccontextmanager
    async def lifespan(self) -> AsyncGenerator[Any, None]:
        """
        Async context manager that initialises the checkpointer on entry and
        cleanly closes the database connection on exit.

        Designed to be used inside the FastAPI ``lifespan`` context::

            async with pg_checkpointer.lifespan() as saver:
                app.state.graph = graph.compile(checkpointer=saver)
                yield   # app runs here

        Yields:
            The ``AsyncPostgresSaver`` instance.
        """
        saver = await self._setup()
        try:
            yield saver
        finally:
            # Close the underlying psycopg connection
            if hasattr(saver, "conn") and saver.conn:
                try:
                    await saver.conn.close()
                    log.info("postgres_checkpointer_connection_closed")
                except Exception as exc:
                    log.warning("postgres_checkpointer_close_error", error=str(exc))


# ---------------------------------------------------------------------------
# Redis checkpointer (optional)
# ---------------------------------------------------------------------------

class RedisCheckpointer:
    """
    Wrapper around ``langgraph_checkpoint_redis.AsyncRedisSaver``.

    Use this when you need fast checkpoint reads/writes (Redis is faster than
    Postgres for checkpointing) but you already have Redis in your stack.

    State is stored in Redis sorted sets keyed by thread ID and checkpoint ID.
    Redis TTL settings control automatic expiry.

    Requires: ``langgraph-checkpoint-redis``
    """

    def __init__(self, redis_url: str) -> None:
        self._redis_url = redis_url
        self._saver: Any = None

    async def get_saver(self) -> Any:
        """Return the initialised ``AsyncRedisSaver``."""
        if self._saver is not None:
            return self._saver

        try:
            from langgraph.checkpoint.redis.aio import AsyncRedisSaver

            self._saver = AsyncRedisSaver(self._redis_url)
            await self._saver.setup()
            log.info("redis_checkpointer_ready")
        except ImportError as exc:
            raise RuntimeError(
                "langgraph-checkpoint-redis is not installed. "
                "Run: pip install langgraph-checkpoint-redis"
            ) from exc

        return self._saver


# ---------------------------------------------------------------------------
# Factory function  (public API)
# ---------------------------------------------------------------------------

async def get_checkpointer(settings: "Settings") -> Any:
    """
    Return the appropriate ``BaseCheckpointSaver`` based on settings.

    Selection logic::

        settings.checkpointer_backend == "memory"   → MemorySaver (built-in)
        settings.checkpointer_backend == "postgres"  → AsyncPostgresSaver
        settings.checkpointer_backend == "redis"     → AsyncRedisSaver

    This is the function called by the FastAPI lifespan to initialise the
    checkpointer once at startup.

    Args:
        settings: The application ``Settings`` instance.

    Returns:
        A ``BaseCheckpointSaver`` compatible with LangGraph's
        ``StateGraph.compile(checkpointer=...)``.

    Raises:
        ValueError: If an unsupported backend is specified.
        RuntimeError: If the required package is not installed.
    """
    from config import CheckpointerBackend

    backend = settings.checkpointer_backend

    if backend == CheckpointerBackend.MEMORY:
        return get_memory_checkpointer()

    elif backend == CheckpointerBackend.POSTGRES:
        cp = PostgresCheckpointer(settings)
        saver = await cp.get_saver()
        log.info("checkpointer_ready", backend="postgres")
        return saver

    elif backend == CheckpointerBackend.REDIS:
        cp = RedisCheckpointer(settings.redis_url)
        saver = await cp.get_saver()
        log.info("checkpointer_ready", backend="redis")
        return saver

    else:
        raise ValueError(
            f"Unsupported checkpointer backend: {backend!r}. "
            "Choose from: memory | postgres | redis"
        )


@asynccontextmanager
async def checkpoint_context(settings: "Settings") -> AsyncGenerator[Any, None]:
    """
    Async context manager that provides a checkpointer for the duration of a
    block and cleans up resources on exit.

    Designed for use in application startup / test fixtures::

        async with checkpoint_context(settings) as checkpointer:
            compiled_graph = graph.compile(checkpointer=checkpointer)
            result = await compiled_graph.ainvoke(initial_state, config=config)

    Yields:
        The initialised checkpointer instance.
    """
    from config import CheckpointerBackend

    if settings.checkpointer_backend == CheckpointerBackend.POSTGRES:
        pg = PostgresCheckpointer(settings)
        async with pg.lifespan() as saver:
            yield saver
    else:
        # Memory and Redis savers have no async teardown needed
        saver = await get_checkpointer(settings)
        yield saver
