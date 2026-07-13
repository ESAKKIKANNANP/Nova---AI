# =============================================================================
# Dockerfile
#
# Multi-stage build for the FastAPI backend.
#
# Stages:
#   1. base     — shared Python + uv setup
#   2. builder  — installs all Python dependencies into an isolated venv
#   3. runtime  — lean final image; copies only the venv + app source
#
# Security hardening:
#   - Non-root user "appuser" runs the process
#   - No dev dependencies in the final image
#   - Build secrets (SECRET_KEY etc.) are injected at runtime, not baked in
#
# Usage:
#   docker build -t ads-backend:latest .
#   docker run --env-file .env -p 8000:8000 ads-backend:latest
# =============================================================================

# ── Stage 1: base ────────────────────────────────────────────────────────────
FROM python:3.12-slim AS base

# Prevent Python from writing .pyc files and enable unbuffered stdout/stderr
# so logs are visible immediately in Docker.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    # Tell uv where to install the virtual environment
    UV_PROJECT_ENVIRONMENT=/opt/venv \
    # Disable uv's automatic venv creation (we manage it explicitly)
    UV_NO_SYNC=1

# Install system-level runtime dependencies.
# --no-install-recommends keeps the layer as small as possible.
RUN apt-get update && apt-get install -y --no-install-recommends \
        curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv (the fast Python package manager) from the official image.
# Pinning to a specific version ensures reproducible builds.
COPY --from=ghcr.io/astral-sh/uv:0.4.18 /uv /usr/local/bin/uv

# ── Stage 2: builder ─────────────────────────────────────────────────────────
FROM base AS builder

WORKDIR /build

# Copy only the dependency manifest first so Docker can cache the install
# layer and skip it on subsequent builds when only app code changes.
COPY pyproject.toml uv.lock* ./

# Create the virtual environment and install production dependencies only.
# --no-dev skips dev/test extras (ruff, pytest, mypy, etc.)
RUN uv venv /opt/venv && \
    uv sync --frozen --no-dev

# ── Stage 3: runtime ─────────────────────────────────────────────────────────
FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    # Point PATH at the venv so all `python` / `uvicorn` calls use it
    PATH="/opt/venv/bin:$PATH" \
    # Default to production log format; override via env-var
    LOG_FORMAT=json \
    ENV=production

# Create a non-root user and group for the application process.
# Running as root inside a container is a security anti-pattern.
RUN groupadd --system appgroup && \
    useradd --system --gid appgroup --no-create-home appuser

WORKDIR /app

# Copy the fully-installed virtual environment from the builder stage.
COPY --from=builder --chown=appuser:appgroup /opt/venv /opt/venv

# Copy application source.  Done after venv copy so app-code changes don't
# invalidate the (expensive) dependency install layer.
COPY --chown=appuser:appgroup app/ ./app/

# Switch to the non-root user before the process starts.
USER appuser

# Expose the application port (informational — actual binding via env-var).
EXPOSE 8000

# Health check so Docker / Kubernetes knows when the container is ready.
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Production entrypoint: gunicorn with uvicorn workers.
# Configuration via environment variables — no flags hard-coded here.
CMD ["gunicorn", "app.main:app", \
     "--worker-class", "uvicorn.workers.UvicornWorker", \
     "--bind", "0.0.0.0:8000", \
     "--workers", "2", \
     "--timeout", "60", \
     "--graceful-timeout", "30", \
     "--access-logfile", "-", \
     "--error-logfile", "-", \
     "--log-level", "info"]
