# =============================================================================
# tests/conftest.py
#
# pytest fixtures shared across the entire test suite.
#
# What's here:
#   - `anyio_backend` — configures pytest-anyio to use asyncio.
#   - `test_settings` — a Settings instance with safe, deterministic values
#                        so tests don't depend on .env files or real secrets.
#   - `app`           — a fresh FastAPI application built with `test_settings`.
#   - `client`        — an `httpx.AsyncClient` wired to the test app via
#                        ASGI transport (no real network calls).
#   - `override_settings` — helper fixture that registers a DI override so
#                            routes receive `test_settings` from Depends(get_settings).
#
# Usage in a test file:
#
#   async def test_something(client: AsyncClient) -> None:
#       response = await client.get("/health")
#       assert response.status_code == 200
#
# Test isolation:
#   Each test gets its own `client` fixture instance; the `app` fixture is
#   function-scoped by default so there is no shared state between tests.
# =============================================================================

from __future__ import annotations

import os
os.environ.setdefault("OPENAI_API_KEY", "mock-key")

from typing import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient

from app.config import Settings, get_settings
from app.main import create_app


# ---------------------------------------------------------------------------
# anyio backend
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def anyio_backend() -> str:
    """Use asyncio as the anyio backend for all async tests."""
    return "asyncio"


# ---------------------------------------------------------------------------
# Test settings
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def test_settings() -> Settings:
    """
    Return a Settings instance with deterministic, test-safe values.

    These values are hard-coded here — they do NOT read from .env so tests
    are fully reproducible regardless of the developer's local environment.
    """
    return Settings(
        app_name="Test API",
        app_version="0.0.0-test",
        env="development",           # type: ignore[arg-type]
        debug=True,
        log_level="DEBUG",           # type: ignore[arg-type]
        log_format="console",        # type: ignore[arg-type]
        secret_key="test-secret-key-not-for-production",
        allowed_origins=["http://testclient"],
        api_v1_prefix="/api/v1",
        host="127.0.0.1",
        port=8000,
    )


# ---------------------------------------------------------------------------
# FastAPI application
# ---------------------------------------------------------------------------

@pytest.fixture()
def app_instance(test_settings: Settings):
    """
    Create a fresh FastAPI application for each test.

    The DI override ensures that any route using `Depends(get_settings)`
    receives `test_settings` instead of the cached production singleton.
    """
    application = create_app(settings=test_settings)
    # Override the DI provider so the cached `get_settings` singleton is
    # not used inside route handlers during tests.
    application.dependency_overrides[get_settings] = lambda: test_settings
    return application


# ---------------------------------------------------------------------------
# Async HTTP client
# ---------------------------------------------------------------------------

@pytest.fixture()
async def client(app_instance) -> AsyncGenerator[AsyncClient, None]:
    """
    Provide an async HTTPX client wired to the test FastAPI app.

    Uses ASGI transport — no real TCP socket is opened, so tests run
    instantly and work offline.

    The `base_url` is arbitrary but required by httpx.
    """
    async with AsyncClient(
        transport=ASGITransport(app=app_instance),
        base_url="http://testserver",
    ) as async_client:
        yield async_client
