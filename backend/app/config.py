# =============================================================================
# app/config.py
#
# Centralised, type-safe configuration using pydantic-settings.
#
# How it works:
#   1. pydantic-settings reads values from the environment and / or a .env
#      file (priority: env-var > .env file > field default).
#   2. Every field is annotated with a Python type — pydantic validates and
#      coerces the raw string values automatically.
#   3. The module exposes a `get_settings()` function decorated with
#      @lru_cache so the Settings object is constructed exactly once per
#      process (cheap singleton without global state).
#   4. FastAPI dependency-injection (`Depends(get_settings)`) can inject the
#      Settings object into any route or middleware.
#
# Adding a new setting:
#   1. Declare the field in `Settings` with a type annotation and default.
#   2. Add the corresponding entry to .env.example with a comment.
#   3. No other changes needed — pydantic-settings handles the rest.
# =============================================================================

from __future__ import annotations

import json
from enum import StrEnum
from functools import lru_cache
from typing import Annotated

from pydantic import AnyHttpUrl, BeforeValidator, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


# ---------------------------------------------------------------------------
# Enum definitions — constrain free-text env-vars to known values
# ---------------------------------------------------------------------------

class Environment(StrEnum):
    """Deployment environment identifier."""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class LogLevel(StrEnum):
    """Python logging level names accepted from the environment."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class LogFormat(StrEnum):
    """Structlog renderer to use."""
    JSON = "json"       # Machine-readable — use in staging / production
    CONSOLE = "console" # Human-readable — use in development


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _parse_cors_origins(value: str | list[str]) -> list[str]:
    """
    Accept ALLOWED_ORIGINS as either:
      - A JSON array string:  '["http://localhost:3000"]'
      - A plain comma-separated string:  'http://localhost:3000,http://localhost:5173'
      - An already-parsed list (when called programmatically)
    """
    if isinstance(value, list):
        return value
    try:
        parsed = json.loads(value)
        if isinstance(parsed, list):
            return [str(o) for o in parsed]
    except (json.JSONDecodeError, ValueError):
        pass
    return [origin.strip() for origin in value.split(",") if origin.strip()]


# Annotated type that runs `_parse_cors_origins` before pydantic validation.
CORSOrigins = Annotated[list[str], BeforeValidator(_parse_cors_origins)]


# ---------------------------------------------------------------------------
# Settings model
# ---------------------------------------------------------------------------

class Settings(BaseSettings):
    """
    Application settings backed by environment variables.

    All fields map 1-to-1 to an environment variable with the same name
    (case-insensitive).  Refer to .env.example for documentation on each
    variable.
    """

    model_config = SettingsConfigDict(
        # Read from .env file when present (ignored if file missing).
        env_file=".env",
        env_file_encoding="utf-8",
        # Ignore extra env-vars that don't map to a field (avoids noise).
        extra="ignore",
        # Freeze the object so Settings instances are hashable and cacheable.
        frozen=True,
        # Case-insensitive matching (APP_NAME == app_name).
        case_sensitive=False,
    )

    # ── Application identity ─────────────────────────────────────────────────
    app_name: str = Field(
        default="Autonomous Data Scientist API",
        description="Human-readable name shown in OpenAPI docs and log records.",
    )
    app_version: str = Field(
        default="0.1.0",
        description="Semantic version string (shown in /health and OpenAPI docs).",
    )
    env: Environment = Field(
        default=Environment.DEVELOPMENT,
        description="Deployment environment (development | staging | production).",
    )
    debug: bool = Field(
        default=False,
        description="Enable FastAPI debug mode. MUST be False in production.",
    )

    # ── Server binding ───────────────────────────────────────────────────────
    host: str = Field(default="0.0.0.0", description="Bind interface for ASGI server.")
    port: int = Field(default=8000, ge=1, le=65535, description="TCP port for ASGI server.")
    workers: int = Field(default=1, ge=1, description="Number of gunicorn worker processes.")

    # ── API routing ──────────────────────────────────────────────────────────
    api_v1_prefix: str = Field(
        default="/api/v1",
        description="URL prefix for all v1 routes.",
    )

    # ── Logging ──────────────────────────────────────────────────────────────
    log_level: LogLevel = Field(default=LogLevel.INFO, description="Minimum log level emitted.")
    log_format: LogFormat = Field(
        default=LogFormat.JSON,
        description="Log renderer: 'json' for production, 'console' for development.",
    )

    # ── CORS ─────────────────────────────────────────────────────────────────
    allowed_origins: CORSOrigins = Field(
        default=["http://localhost:3000"],
        description="List of allowed CORS origins.",
    )
    allow_credentials: bool = Field(default=True)
    allowed_methods: CORSOrigins = Field(default=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"])
    allowed_headers: CORSOrigins = Field(default=["*"])

    # ── Security ─────────────────────────────────────────────────────────────
    secret_key: str = Field(
        default="CHANGE_ME",
        description="Secret key for signing tokens. MUST be overridden in production.",
    )
    access_token_expire_minutes: int = Field(default=30, ge=1)

    # ── Computed / derived properties ────────────────────────────────────────

    @property
    def is_production(self) -> bool:
        """True when running in the production environment."""
        return self.env == Environment.PRODUCTION

    @property
    def is_development(self) -> bool:
        """True when running in the development environment."""
        return self.env == Environment.DEVELOPMENT

    @field_validator("secret_key")
    @classmethod
    def warn_insecure_secret(cls, v: str) -> str:
        """Emit a warning if the default secret key is used outside development."""
        if v == "CHANGE_ME":
            import warnings
            warnings.warn(
                "SECRET_KEY is set to the insecure default value. "
                "Set a strong random key in production using: "
                "openssl rand -hex 32",
                stacklevel=2,
            )
        return v


# ---------------------------------------------------------------------------
# Cached factory — call this everywhere instead of instantiating Settings()
# ---------------------------------------------------------------------------

@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """
    Return the application Settings singleton.

    The @lru_cache decorator ensures Settings() is constructed only once per
    process, even when used as a FastAPI dependency across hundreds of
    concurrent requests.

    Usage in a route:
        from fastapi import Depends
        from app.config import Settings, get_settings

        @router.get("/example")
        async def example(settings: Annotated[Settings, Depends(get_settings)]):
            return {"app": settings.app_name}

    Usage in tests (override the cache):
        from app.config import get_settings
        app.dependency_overrides[get_settings] = lambda: Settings(secret_key="test")
    """
    return Settings()
