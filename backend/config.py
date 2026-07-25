# =============================================================================
# config.py  (backend/config.py)
#
# Centralised configuration for the Autonomous Data Scientist backend.
#
# Architecture
# ─────────────
# All runtime settings are modelled as a single Pydantic ``Settings`` class
# (powered by pydantic-settings).  Values are loaded from three sources in
# descending priority:
#
#   1. Environment variables  ← highest priority (12-factor)
#   2. .env file              ← local developer overrides
#   3. Field defaults         ← safe values baked into the class
#
# The ``get_settings()`` function is the FastAPI DI provider.  It caches the
# singleton via ``@lru_cache`` so the .env file is parsed exactly once per
# process.  Tests override it with ``app.dependency_overrides``.
#
# Sections
# ─────────
#   AppSettings     — name, version, env, debug
#   ServerSettings  — host, port, workers
#   APISettings     — prefix, CORS
#   SecuritySettings — secret key, token expiry
#   DatabaseSettings — PostgreSQL URLs
#   RedisSettings   — connection URL, pool size
#   LLMSettings     — provider selection, API keys, model names, timeouts
#   LangGraphSettings — graph-specific knobs (retry limit, checkpointer backend)
#   MemorySettings  — ChromaDB / vector store config
#   StorageSettings — S3 / MinIO object-store config
#   ObservabilitySettings — LangSmith tracing, log level/format
#   Settings        — composed mega-class exported to the rest of the app
# =============================================================================

from __future__ import annotations

import os
from enum import Enum
from functools import lru_cache
from typing import Any

from pydantic import Field, PostgresDsn, RedisDsn, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


# ---------------------------------------------------------------------------
# Enumerations  (prevent magic-string bugs throughout the codebase)
# ---------------------------------------------------------------------------

class Environment(str, Enum):
    """Deployment environment.  Controls log format and debug behaviour."""
    DEVELOPMENT = "development"
    STAGING     = "staging"
    PRODUCTION  = "production"


class LogLevel(str, Enum):
    """Standard Python log levels accepted as config strings."""
    DEBUG    = "DEBUG"
    INFO     = "INFO"
    WARNING  = "WARNING"
    ERROR    = "ERROR"
    CRITICAL = "CRITICAL"


class LogFormat(str, Enum):
    """
    Structured log output format.

    ``console`` — human-readable coloured output (development).
    ``json``    — machine-parseable JSON (production / log aggregators).
    """
    CONSOLE = "console"
    JSON    = "json"


class LLMProvider(str, Enum):
    """Supported LLM backend providers."""
    OPENAI  = "openai"
    GEMINI  = "gemini"
    OLLAMA  = "ollama"   # local OSS via Ollama server
    VLLM    = "vllm"     # local OSS via vLLM server


class CheckpointerBackend(str, Enum):
    """
    Storage backend for the LangGraph checkpointer.

    ``memory``   — in-process dict; no persistence (unit tests / dev).
    ``postgres`` — ``langgraph-checkpoint-postgres`` (production).
    ``redis``    — ``langgraph-checkpoint-redis`` (optional).
    """
    MEMORY   = "memory"
    POSTGRES = "postgres"
    REDIS    = "redis"


# ---------------------------------------------------------------------------
# Setting groups — each inherits BaseSettings so they can be composed
# ---------------------------------------------------------------------------

class AppSettings(BaseSettings):
    """Core application identity settings."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = Field(
        default="Autonomous Data Scientist API",
        description="Human-readable name surfaced in OpenAPI docs and logs.",
    )
    app_version: str = Field(
        default="0.1.0",
        description="Semantic version string.",
    )
    env: Environment = Field(
        default=Environment.DEVELOPMENT,
        description="Deployment environment (development | staging | production).",
    )
    debug: bool = Field(
        default=False,
        description="Enable FastAPI debug mode.  MUST be False in production.",
    )


class ServerSettings(BaseSettings):
    """HTTP server binding configuration."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    host: str    = Field(default="0.0.0.0", description="Interface to listen on.")
    port: int    = Field(default=8000,       description="TCP port.")
    workers: int = Field(default=1,          description="Gunicorn worker count.")


class APISettings(BaseSettings):
    """API routing and CORS configuration."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    api_v1_prefix: str = Field(
        default="/api/v1",
        description="URL prefix for all v1 routes.",
    )
    allowed_origins: list[str] = Field(
        default=["http://localhost:3000", "http://localhost:5173"],
        description="CORS allowed origins.",
    )
    allow_credentials: bool    = Field(default=True)
    allowed_methods: list[str] = Field(default=["*"])
    allowed_headers: list[str] = Field(default=["*"])


class SecuritySettings(BaseSettings):
    """Authentication and JWT configuration."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    secret_key: str = Field(
        default="CHANGE_ME_IN_PRODUCTION",
        description="HMAC secret for JWT signing. Override via SECRET_KEY env var.",
    )
    access_token_expire_minutes: int = Field(
        default=30,
        description="JWT access token lifetime in minutes.",
    )
    algorithm: str = Field(
        default="HS256",
        description="JWT signing algorithm.",
    )


class DatabaseSettings(BaseSettings):
    """Database connection configuration."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = Field(
        default="sqlite:///./dev.db",
        description="Synchronous SQLAlchemy DSN (used by Alembic migrations).",
    )
    async_database_url: str = Field(
        default="sqlite+aiosqlite:///./dev.db",
        description="Async SQLAlchemy DSN (used by FastAPI request handlers).",
    )
    db_pool_size: int     = Field(default=10,  description="SQLAlchemy pool size.")
    db_max_overflow: int  = Field(default=20,  description="SQLAlchemy max overflow.")
    db_pool_timeout: int  = Field(default=30,  description="Pool checkout timeout (seconds).")
    db_echo: bool         = Field(default=False, description="Log all SQL statements (dev only).")


class RedisSettings(BaseSettings):
    """Redis connection configuration (cache + Celery broker + pub/sub)."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    redis_url: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection URL.",
    )
    redis_pool_size: int       = Field(default=20,  description="Connection pool size.")
    redis_ttl_seconds: int     = Field(default=3600, description="Default key TTL (1 hour).")
    redis_session_ttl: int     = Field(default=86400, description="Session TTL (24 hours).")


class LLMSettings(BaseSettings):
    """LLM provider configuration."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    llm_provider: LLMProvider = Field(
        default=LLMProvider.OPENAI,
        description="Primary LLM provider.  Can be overridden per-agent.",
    )

    # OpenAI
    openai_api_key: str   = Field(default="", description="OpenAI API key.")
    openai_model: str     = Field(default="gpt-4o", description="Default OpenAI model.")
    openai_base_url: str  = Field(
        default="https://api.openai.com/v1",
        description="Override for Azure OpenAI or proxies.",
    )

    # Google Gemini
    gemini_api_key: str   = Field(default="", description="Google AI / Gemini API key.")
    gemini_model: str     = Field(default="gemini-2.0-flash", description="Gemini model name.")

    # Local OSS (Ollama / vLLM)
    local_llm_base_url: str = Field(
        default="http://localhost:11434",
        description="Base URL for Ollama or vLLM server.",
    )
    local_llm_model: str = Field(
        default="llama3.2",
        description="Model name served by the local LLM server.",
    )

    # Shared knobs
    llm_temperature: float    = Field(default=0.0,  description="Sampling temperature (0 = deterministic).")
    llm_max_tokens: int       = Field(default=4096, description="Max output tokens per LLM call.")
    llm_request_timeout: int  = Field(default=120,  description="HTTP timeout for LLM requests (seconds).")
    llm_max_retries: int      = Field(default=3,    description="Retry count on transient LLM errors.")


class LangGraphSettings(BaseSettings):
    """LangGraph-specific configuration."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Checkpointer
    checkpointer_backend: CheckpointerBackend = Field(
        default=CheckpointerBackend.MEMORY,
        description="Persistence backend for LangGraph state snapshots.",
    )

    # Retry / critic loop guard
    max_critic_retries: int = Field(
        default=3,
        description="Maximum number of critic→planner retry loops before "
                    "escalating to human review.",
    )

    # Recursion guard (LangGraph built-in)
    max_graph_recursion: int = Field(
        default=50,
        description="LangGraph recursion_limit passed to graph.invoke().",
    )

    # Streaming
    stream_mode: str = Field(
        default="updates",
        description="LangGraph stream mode: 'values' | 'updates' | 'events'.",
    )

    # Human-in-the-loop timeout
    human_review_timeout_seconds: int = Field(
        default=3600,
        description="Seconds to wait for human input before auto-resuming.",
    )


class MemorySettings(BaseSettings):
    """Vector store / memory configuration."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # ChromaDB (default — embedded, no server required)
    chromadb_host: str = Field(default="localhost",   description="ChromaDB server host.")
    chromadb_port: int = Field(default=8001,           description="ChromaDB server port.")
    chromadb_persist_dir: str = Field(
        default="./data/chromadb",
        description="Local persistence directory for embedded ChromaDB.",
    )

    # Embedding model
    embedding_model: str = Field(
        default="text-embedding-3-small",
        description="OpenAI embedding model used to index memory items.",
    )
    embedding_dimension: int = Field(
        default=1536,
        description="Vector dimension matching the chosen embedding model.",
    )

    # Retrieval
    memory_top_k: int = Field(
        default=5,
        description="Number of memory items retrieved for each agent context.",
    )
    memory_score_threshold: float = Field(
        default=0.7,
        description="Minimum cosine-similarity score to include a memory item.",
    )


class StorageSettings(BaseSettings):
    """Object storage (S3 / MinIO) configuration."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    s3_bucket: str          = Field(default="ads-artifacts", description="Primary S3 bucket name.")
    s3_region: str          = Field(default="us-east-1",     description="AWS region.")
    s3_access_key: str      = Field(default="",              description="AWS / MinIO access key.")
    s3_secret_key: str      = Field(default="",              description="AWS / MinIO secret key.")
    s3_endpoint_url: str    = Field(
        default="",
        description="Override endpoint for MinIO or S3-compatible stores. "
                    "Leave empty to use AWS S3.",
    )
    s3_dataset_prefix: str  = Field(default="datasets/",     description="Prefix for dataset objects.")
    s3_artifact_prefix: str = Field(default="artifacts/",    description="Prefix for output artefacts.")


class ObservabilitySettings(BaseSettings):
    """Logging, tracing, and metrics configuration."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    log_level: LogLevel   = Field(default=LogLevel.INFO,    description="Minimum log level.")
    log_format: LogFormat = Field(default=LogFormat.CONSOLE, description="Log output format.")

    # LangSmith (LLM call tracing)
    langchain_tracing_v2: bool = Field(
        default=False,
        description="Enable LangSmith tracing (set LANGCHAIN_TRACING_V2=true).",
    )
    langchain_api_key: str = Field(default="", description="LangSmith API key.")
    langchain_project: str = Field(
        default="autonomous-data-scientist",
        description="LangSmith project name.",
    )
    langchain_endpoint: str = Field(
        default="https://api.smith.langchain.com",
        description="LangSmith ingestion endpoint.",
    )

    # Prometheus
    enable_metrics: bool = Field(default=True, description="Expose /metrics endpoint.")


# ---------------------------------------------------------------------------
# Composed Settings class
# ---------------------------------------------------------------------------

class Settings(
    AppSettings,
    ServerSettings,
    APISettings,
    SecuritySettings,
    DatabaseSettings,
    RedisSettings,
    LLMSettings,
    LangGraphSettings,
    MemorySettings,
    StorageSettings,
    ObservabilitySettings,
):
    """
    Single composed settings object for the entire backend.

    All setting groups are merged here so that application code only ever
    imports ``Settings`` (or the ``get_settings()`` provider), not individual
    sub-classes.

    Environment variables are read from:
      1. The process environment (highest priority)
      2. A ``.env`` file in the current working directory
      3. Field defaults (fallbacks defined above)

    Usage::

        from backend.config import get_settings
        settings = get_settings()
        print(settings.openai_api_key)
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,    # OPENAI_API_KEY == openai_api_key
        extra="ignore",          # silently drop unknown env vars
    )

    @model_validator(mode="after")
    def _validate_production_secrets(self) -> "Settings":
        """
        Enforce that sensitive secrets are overridden in non-development
        environments.  Raises ``ValueError`` so startup fails fast rather than
        running with insecure defaults.
        """
        if self.env == Environment.PRODUCTION:
            if self.secret_key == "CHANGE_ME_IN_PRODUCTION":
                raise ValueError(
                    "SECRET_KEY must be set to a strong random value in production. "
                    "Generate one with: openssl rand -hex 32"
                )
            if not self.openai_api_key and self.llm_provider == LLMProvider.OPENAI:
                raise ValueError(
                    "OPENAI_API_KEY must be set when llm_provider=openai in production."
                )
        return self

    @property
    def is_production(self) -> bool:
        """Shorthand boolean for production environment checks."""
        return self.env == Environment.PRODUCTION

    @property
    def is_development(self) -> bool:
        """Shorthand boolean for development environment checks."""
        return self.env == Environment.DEVELOPMENT


# ---------------------------------------------------------------------------
# DI provider (singleton via lru_cache)
# ---------------------------------------------------------------------------

@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """
    Return the cached ``Settings`` singleton.

    Called by FastAPI's ``Depends(get_settings)`` in every route that needs
    configuration access.  The ``@lru_cache`` ensures the ``.env`` file is
    parsed exactly once per process; subsequent calls return the same object.

    In tests, override via::

        app.dependency_overrides[get_settings] = lambda: Settings(...)

    Returns:
        The global ``Settings`` instance.
    """
    return Settings()


# ---------------------------------------------------------------------------
# Convenience re-export — direct module-level access for non-DI code
# ---------------------------------------------------------------------------

settings: Settings = get_settings()
"""
Module-level singleton for non-FastAPI code (e.g. Celery workers, CLI tools)
that cannot use FastAPI's DI system.

Prefer ``get_settings()`` inside FastAPI route handlers so that test overrides
work correctly.
"""
