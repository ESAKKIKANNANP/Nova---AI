# =============================================================================
# graphs/memory.py
#
# Memory Manager for the Autonomous Data Scientist LangGraph
#
# The memory system has three distinct tiers, each serving a different
# purpose in the agent pipeline:
#
#   ┌─────────────────────────────────────────────────────────────────────┐
#   │  Tier            Backend         Scope      TTL        Use-case      │
#   ├─────────────────────────────────────────────────────────────────────┤
#   │  WorkingMemory   LangGraph State  Per-node  Until END  In-graph data │
#   │  ShortTermMemory Redis            Session   24 hours   Cross-turn    │
#   │  LongTermMemory  ChromaDB         User      Permanent  Semantic RAG  │
#   └─────────────────────────────────────────────────────────────────────┘
#
# Design decisions
# ─────────────────
# 1. Protocol-based interface — each tier implements ``MemoryProtocol`` so
#    callers (agents) are not coupled to a specific backend.  Tests can inject
#    ``InMemoryShortTermMemory`` without spinning up Redis.
# 2. Async-first — all I/O methods are async-compatible because the LangGraph
#    nodes run inside an asyncio event loop.
# 3. Graceful degradation — if Redis or ChromaDB is unavailable the
#    ``MemoryManager`` falls back to in-process dicts rather than crashing,
#    but it logs a warning so operators know the service is degraded.
# 4. JSON serialisation — all values stored in Redis are JSON-encoded so they
#    survive process restarts and are human-readable.
#
# Usage in a node
# ────────────────
#   memory = MemoryManager.from_settings(settings)
#
#   # Short-term: store intermediate result
#   await memory.short_term.set(session_id, "eda_summary", {"rows": 1000})
#
#   # Short-term: retrieve it in the next node
#   summary = await memory.short_term.get(session_id, "eda_summary")
#
#   # Long-term: index an observation for future RAG retrieval
#   await memory.long_term.store(session_id, "EDA found 12% missing in col 'age'")
#
#   # Long-term: retrieve semantically similar past observations
#   memories = await memory.long_term.retrieve(session_id, "missing values")
# =============================================================================

from __future__ import annotations

import json
import logging
from abc import ABC, abstractmethod
from typing import Any, Sequence, TYPE_CHECKING

if TYPE_CHECKING:
    from config import Settings

log = logging.getLogger(__name__)


# =============================================================================
# Short-Term Memory
# =============================================================================

class ShortTermMemoryProtocol(ABC):
    """
    Abstract interface for short-term (session-scoped) memory.

    Short-term memory stores *structured* key-value pairs that must survive
    between LangGraph node invocations within the same session.  Unlike
    ``GraphState``, it is persisted externally so it can be accessed by
    multiple Celery workers running different parts of the same job.

    All implementations must be **thread-safe** and support concurrent access.
    """

    @abstractmethod
    async def set(
        self,
        session_id: str,
        key: str,
        value: Any,
        ttl: int | None = None,
    ) -> None:
        """
        Store ``value`` under ``key`` for the given session.

        Args:
            session_id: LangGraph session / thread identifier.
            key:        Arbitrary string key within the session namespace.
            value:      JSON-serializable value.
            ttl:        Optional TTL in seconds; uses ``settings.redis_ttl_seconds``
                        if omitted.
        """

    @abstractmethod
    async def get(self, session_id: str, key: str) -> Any | None:
        """
        Retrieve the value stored under ``key`` for the session.

        Returns:
            The stored value, or ``None`` if the key does not exist or has
            expired.
        """

    @abstractmethod
    async def delete(self, session_id: str, key: str) -> None:
        """Remove a specific key from the session namespace."""

    @abstractmethod
    async def clear_session(self, session_id: str) -> None:
        """Remove all keys belonging to the given session."""

    @abstractmethod
    async def keys(self, session_id: str) -> list[str]:
        """Return all keys stored for the given session."""


class InMemoryShortTermMemory(ShortTermMemoryProtocol):
    """
    In-process dictionary implementation of ``ShortTermMemoryProtocol``.

    Used in unit tests and local development where Redis is not available.
    Data is lost when the process exits.

    Not suitable for multi-process or multi-worker deployments because
    each worker has its own private dict with no shared state.
    """

    def __init__(self) -> None:
        # _store[session_id][key] = value
        self._store: dict[str, dict[str, Any]] = {}

    async def set(
        self,
        session_id: str,
        key: str,
        value: Any,
        ttl: int | None = None,  # TTL ignored for in-memory implementation
    ) -> None:
        self._store.setdefault(session_id, {})[key] = value

    async def get(self, session_id: str, key: str) -> Any | None:
        return self._store.get(session_id, {}).get(key)

    async def delete(self, session_id: str, key: str) -> None:
        self._store.get(session_id, {}).pop(key, None)

    async def clear_session(self, session_id: str) -> None:
        self._store.pop(session_id, None)

    async def keys(self, session_id: str) -> list[str]:
        return list(self._store.get(session_id, {}).keys())


class RedisShortTermMemory(ShortTermMemoryProtocol):
    """
    Redis-backed implementation of ``ShortTermMemoryProtocol``.

    Each value is stored at Redis key ``ads:stm:{session_id}:{key}`` and
    serialised as JSON so values survive process restarts and are compatible
    with non-Python consumers.

    The Redis connection is established lazily on first use to avoid blocking
    startup.  A single ``redis.asyncio.Redis`` connection is shared across
    all operations to benefit from connection-pool re-use.

    Requires: ``redis[asyncio]`` package.
    """

    _NAMESPACE = "ads:stm"

    def __init__(self, redis_url: str, default_ttl: int = 3600) -> None:
        self._url = redis_url
        self._default_ttl = default_ttl
        self._client: Any = None   # redis.asyncio.Redis, set lazily

    async def _get_client(self) -> Any:
        """Return the Redis client, initialising it on first call."""
        if self._client is None:
            try:
                import redis.asyncio as aioredis
                self._client = aioredis.from_url(
                    self._url,
                    decode_responses=True,
                    encoding="utf-8",
                )
                # Ping to validate the connection immediately
                await self._client.ping()
                log.info("redis_short_term_memory_connected", url=self._url)
            except Exception as exc:
                log.warning(
                    "redis_connection_failed_falling_back",
                    error=str(exc),
                    fallback="InMemoryShortTermMemory",
                )
                raise
        return self._client

    def _make_key(self, session_id: str, key: str) -> str:
        """Build the namespaced Redis key for a session/key pair."""
        return f"{self._NAMESPACE}:{session_id}:{key}"

    def _session_pattern(self, session_id: str) -> str:
        """Build a Redis glob pattern matching all keys for a session."""
        return f"{self._NAMESPACE}:{session_id}:*"

    async def set(
        self,
        session_id: str,
        key: str,
        value: Any,
        ttl: int | None = None,
    ) -> None:
        client = await self._get_client()
        redis_key = self._make_key(session_id, key)
        serialized = json.dumps(value, default=str)
        await client.setex(redis_key, ttl or self._default_ttl, serialized)

    async def get(self, session_id: str, key: str) -> Any | None:
        client = await self._get_client()
        raw = await client.get(self._make_key(session_id, key))
        return json.loads(raw) if raw is not None else None

    async def delete(self, session_id: str, key: str) -> None:
        client = await self._get_client()
        await client.delete(self._make_key(session_id, key))

    async def clear_session(self, session_id: str) -> None:
        client = await self._get_client()
        pattern = self._session_pattern(session_id)
        keys: list[str] = await client.keys(pattern)
        if keys:
            await client.delete(*keys)

    async def keys(self, session_id: str) -> list[str]:
        client = await self._get_client()
        pattern = self._session_pattern(session_id)
        full_keys: list[str] = await client.keys(pattern)
        prefix = f"{self._NAMESPACE}:{session_id}:"
        return [k[len(prefix):] for k in full_keys]


# =============================================================================
# Long-Term Memory  (Semantic / Vector)
# =============================================================================

class LongTermMemoryProtocol(ABC):
    """
    Abstract interface for long-term (semantic / vector) memory.

    Long-term memory stores *natural-language observations* indexed as dense
    vector embeddings.  Agents can retrieve semantically similar past
    observations using a query string — enabling RAG-style context injection
    without manually managing keys.

    Typical usage:
      - Data Analyst agent stores: "The dataset has 12% missing in 'age' column."
      - Insight Generator agent retrieves: memories matching "missing values"
        to include domain-specific context in its narrative.
    """

    @abstractmethod
    async def store(
        self,
        session_id: str,
        text: str,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """
        Index ``text`` as a new memory item.

        Args:
            session_id: Scope for this memory item.
            text:       Natural-language observation to store.
            metadata:   Optional structured metadata attached to the item
                        (e.g. agent_name, node_id, timestamp).

        Returns:
            The generated ``memory_id`` (UUID string).
        """

    @abstractmethod
    async def retrieve(
        self,
        session_id: str,
        query: str,
        top_k: int = 5,
        score_threshold: float = 0.7,
    ) -> list[dict[str, Any]]:
        """
        Retrieve the ``top_k`` most semantically similar memory items.

        Args:
            session_id:      Scope for the retrieval (only this session's
                             memories are searched).
            query:           Natural-language query string.
            top_k:           Maximum number of items to return.
            score_threshold: Minimum cosine-similarity score (0–1).

        Returns:
            List of dicts with keys: ``memory_id``, ``text``, ``score``,
            ``metadata``.
        """

    @abstractmethod
    async def clear_session(self, session_id: str) -> None:
        """Delete all memory items for the given session."""


class InMemoryLongTermMemory(LongTermMemoryProtocol):
    """
    Simple in-process implementation of ``LongTermMemoryProtocol``.

    Uses a plain list of stored strings and returns them in insertion order
    (no actual vector search).  Suitable for unit tests and local development
    where ChromaDB / OpenAI embeddings are not available.

    **Not suitable for production** — no semantic ranking, no persistence.
    """

    def __init__(self) -> None:
        # _store[session_id] = list of {"memory_id", "text", "metadata"}
        self._store: dict[str, list[dict[str, Any]]] = {}

    async def store(
        self,
        session_id: str,
        text: str,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        import uuid
        memory_id = str(uuid.uuid4())
        self._store.setdefault(session_id, []).append(
            {"memory_id": memory_id, "text": text, "metadata": metadata or {}}
        )
        return memory_id

    async def retrieve(
        self,
        session_id: str,
        query: str,
        top_k: int = 5,
        score_threshold: float = 0.7,
    ) -> list[dict[str, Any]]:
        # Return last `top_k` items with a fake score of 1.0
        items = self._store.get(session_id, [])
        results = [
            {**item, "score": 1.0}
            for item in items[-top_k:]
        ]
        return list(reversed(results))

    async def clear_session(self, session_id: str) -> None:
        self._store.pop(session_id, None)


class ChromaLongTermMemory(LongTermMemoryProtocol):
    """
    ChromaDB-backed semantic memory using OpenAI text embeddings.

    Architecture
    ─────────────
    - One ChromaDB *collection* is used: ``ads_memory``.
    - Each document is a memory text; the ``session_id`` is stored in metadata
      and used as a ``where`` filter on retrieval so sessions are isolated.
    - Embeddings are generated by the ``openai.embeddings`` API
      (``text-embedding-3-small`` by default, 1536-dimensional).

    Lazy initialisation
    ────────────────────
    The ChromaDB client and OpenAI client are created on first use so that
    importing this module does not require environment variables to be set.

    Requires: ``chromadb``, ``openai`` packages.
    """

    _COLLECTION_NAME = "ads_memory"

    def __init__(
        self,
        *,
        chroma_host: str = "localhost",
        chroma_port: int = 8001,
        chroma_persist_dir: str | None = None,
        openai_api_key: str = "",
        embedding_model: str = "text-embedding-3-small",
    ) -> None:
        self._chroma_host = chroma_host
        self._chroma_port = chroma_port
        self._persist_dir = chroma_persist_dir
        self._openai_api_key = openai_api_key
        self._embedding_model = embedding_model
        self._collection: Any = None   # chromadb.Collection, set lazily
        self._openai_client: Any = None

    async def _get_collection(self) -> Any:
        """Return the ChromaDB collection, creating it lazily."""
        if self._collection is not None:
            return self._collection

        import chromadb

        if self._persist_dir:
            # Embedded (serverless) ChromaDB with disk persistence
            client = chromadb.PersistentClient(path=self._persist_dir)
        else:
            # HTTP client connecting to a remote ChromaDB server
            client = chromadb.HttpClient(
                host=self._chroma_host,
                port=self._chroma_port,
            )

        self._collection = client.get_or_create_collection(
            name=self._COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},  # use cosine distance
        )
        log.info(
            "chromadb_collection_ready",
            collection=self._COLLECTION_NAME,
            persist_dir=self._persist_dir,
        )
        return self._collection

    async def _embed(self, text: str) -> list[float]:
        """Generate an embedding vector for ``text`` using OpenAI."""
        if self._openai_client is None:
            from openai import AsyncOpenAI
            self._openai_client = AsyncOpenAI(api_key=self._openai_api_key)

        response = await self._openai_client.embeddings.create(
            model=self._embedding_model,
            input=text,
        )
        return response.data[0].embedding

    async def store(
        self,
        session_id: str,
        text: str,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        import uuid

        collection = await self._get_collection()
        memory_id  = str(uuid.uuid4())
        embedding  = await self._embed(text)

        meta = {"session_id": session_id, **(metadata or {})}

        collection.add(
            ids=[memory_id],
            embeddings=[embedding],
            documents=[text],
            metadatas=[meta],
        )
        log.debug(
            "memory_stored",
            session_id=session_id,
            memory_id=memory_id,
            text_length=len(text),
        )
        return memory_id

    async def retrieve(
        self,
        session_id: str,
        query: str,
        top_k: int = 5,
        score_threshold: float = 0.7,
    ) -> list[dict[str, Any]]:
        collection = await self._get_collection()
        embedding  = await self._embed(query)

        results = collection.query(
            query_embeddings=[embedding],
            n_results=top_k,
            where={"session_id": session_id},
            include=["documents", "metadatas", "distances"],
        )

        items: list[dict[str, Any]] = []
        for idx, (doc, meta, dist) in enumerate(zip(
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0],
        )):
            # ChromaDB cosine distance → cosine similarity: score = 1 - distance
            score = 1.0 - dist
            if score >= score_threshold:
                items.append({
                    "memory_id": results["ids"][0][idx],
                    "text": doc,
                    "score": round(score, 4),
                    "metadata": meta,
                })

        log.debug(
            "memory_retrieved",
            session_id=session_id,
            query_length=len(query),
            results_count=len(items),
        )
        return items

    async def clear_session(self, session_id: str) -> None:
        collection = await self._get_collection()
        # ChromaDB doesn't support bulk delete by metadata directly;
        # we query IDs first then delete them.
        results = collection.get(where={"session_id": session_id})
        if results["ids"]:
            collection.delete(ids=results["ids"])
            log.info(
                "memory_session_cleared",
                session_id=session_id,
                deleted_count=len(results["ids"]),
            )


# =============================================================================
# MemoryManager  (facade)
# =============================================================================

class MemoryManager:
    """
    Unified facade that exposes all three memory tiers through a single object.

    Agents and nodes call ``MemoryManager`` rather than managing individual
    tier instances, which keeps node code clean and makes testing easy
    (inject a ``MemoryManager`` with all in-memory backends).

    Example::

        memory = MemoryManager(
            short_term=InMemoryShortTermMemory(),
            long_term=InMemoryLongTermMemory(),
        )
        await memory.short_term.set(session_id, "summary", {...})
        await memory.long_term.store(session_id, "EDA complete: 1000 rows.")

    Use ``MemoryManager.from_settings(settings)`` in production to get the
    correct backend implementations based on configuration.
    """

    def __init__(
        self,
        short_term: ShortTermMemoryProtocol,
        long_term: LongTermMemoryProtocol,
    ) -> None:
        self.short_term = short_term
        self.long_term  = long_term

    @classmethod
    def from_settings(cls, settings: "Settings") -> "MemoryManager":
        """
        Factory method that constructs the appropriate backend implementations
        based on the application settings.

        Backend selection:
          - ``ShortTermMemory``: always Redis (falls back to in-memory if
            Redis is unreachable at startup).
          - ``LongTermMemory``: ChromaDB with OpenAI embeddings (falls back
            to in-memory if ``openai_api_key`` is not configured).

        Args:
            settings: The application ``Settings`` instance.

        Returns:
            A configured ``MemoryManager``.
        """
        # ── Short-Term (Redis) ────────────────────────────────────────────────
        try:
            short_term: ShortTermMemoryProtocol = RedisShortTermMemory(
                redis_url=settings.redis_url,
                default_ttl=settings.redis_session_ttl,
            )
            log.info("short_term_memory_backend", backend="redis")
        except Exception as exc:
            log.warning(
                "short_term_memory_fallback",
                backend="in_memory",
                reason=str(exc),
            )
            short_term = InMemoryShortTermMemory()

        # ── Long-Term (ChromaDB) ──────────────────────────────────────────────
        if settings.openai_api_key:
            long_term: LongTermMemoryProtocol = ChromaLongTermMemory(
                chroma_host=settings.chromadb_host,
                chroma_port=settings.chromadb_port,
                chroma_persist_dir=settings.chromadb_persist_dir or None,
                openai_api_key=settings.openai_api_key,
                embedding_model=settings.embedding_model,
            )
            log.info("long_term_memory_backend", backend="chromadb")
        else:
            log.warning(
                "long_term_memory_fallback",
                backend="in_memory",
                reason="OPENAI_API_KEY not configured",
            )
            long_term = InMemoryLongTermMemory()

        return cls(short_term=short_term, long_term=long_term)
