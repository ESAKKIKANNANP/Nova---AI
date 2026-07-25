# =============================================================================
# backend/README.md
#
# Quick-start guide for the FastAPI backend.
# =============================================================================

# Autonomous Data Scientist — FastAPI Backend

Production-ready FastAPI backend scaffold for the **Autonomous Data Scientist** platform.

---

## Tech Stack

| Layer | Tool |
|---|---|
| Language | Python 3.12 |
| Package manager | [uv](https://docs.astral.sh/uv/) |
| Web framework | FastAPI 0.111 |
| ASGI server | Uvicorn |
| Config | `pydantic-settings` |
| Structured logging | `structlog` |
| Testing | `pytest` + `httpx` |
| Linting / formatting | `ruff` |
| Type checking | `mypy` |

---

## Project Structure

```
backend/
├── pyproject.toml          # uv project manifest (deps, ruff, pytest, mypy)
├── .env.example            # documented environment variable template
├── app/
│   ├── main.py             # FastAPI app factory + lifespan hooks
│   ├── config.py           # pydantic-settings Settings class
│   ├── logging_config.py   # structlog bootstrap
│   ├── dependencies.py     # reusable DI providers
│   ├── exceptions.py       # exception hierarchy + handlers
│   ├── middleware/
│   │   ├── correlation_id.py   # X-Correlation-ID propagation
│   │   └── request_logging.py  # structured HTTP access log
│   ├── routers/
│   │   └── health.py       # GET /health + GET /readiness
│   └── schemas/
│       ├── common.py       # ResponseEnvelope[T], MetaResponse
│       └── health.py       # HealthResponse, ReadinessResponse
└── tests/
    ├── conftest.py         # shared pytest fixtures
    ├── test_health.py      # health endpoint tests
    └── test_middleware.py  # middleware tests
```

---

## Quick Start (Local)

### Prerequisites

Install [uv](https://docs.astral.sh/uv/getting-started/installation/):

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 1. Install dependencies

```bash
cd backend
uv sync
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env — at minimum set SECRET_KEY to a strong random value
```

### 3. Run the development server

```bash
ENV=development DEBUG=true DATABASE_URL=sqlite:///./dev.db ASYNC_DATABASE_URL=sqlite+aiosqlite:///./dev.db \
  uv run uvicorn main:app --host 127.0.0.1 --port 8000
```

### 4. Verify

| URL | Description |
|---|---|
| http://localhost:8000/health | Liveness probe |
| http://localhost:8000/readiness | Readiness probe |
| http://localhost:8000/docs | Swagger UI |
| http://localhost:8000/redoc | ReDoc UI |
| http://localhost:8000/openapi.json | OpenAPI schema |

---

## Running Tests

```bash
cd backend
uv run pytest
```

With coverage report:

```bash
uv run pytest --cov=app --cov-report=html
open htmlcov/index.html
```

---

## Code Quality

```bash
# Lint
uv run ruff check app tests

# Format
uv run ruff format app tests

# Type check
uv run mypy app
```

---

## Environment Variables

See [.env.example](.env.example) for the full list with inline documentation.

| Variable | Default | Description |
|---|---|---|
| `APP_NAME` | `Autonomous Data Scientist API` | Service name in logs and docs |
| `APP_VERSION` | `0.1.0` | Version shown in /health and OpenAPI |
| `ENV` | `development` | `development` / `staging` / `production` |
| `DEBUG` | `false` | FastAPI debug mode |
| `LOG_LEVEL` | `INFO` | Minimum log level |
| `LOG_FORMAT` | `json` | `json` (prod) or `console` (dev) |
| `ALLOWED_ORIGINS` | `["http://localhost:3000"]` | CORS allowed origins |
| `SECRET_KEY` | `CHANGE_ME` | **Must be overridden in production** |
| `HOST` | `127.0.0.1` | ASGI bind address |
| `PORT` | `8000` | ASGI bind port |

---

## Adding a New Route

1. Create `app/routers/my_feature.py` — define a `router = APIRouter(...)`.
2. Add Pydantic schemas to `app/schemas/my_feature.py`.
3. Register in `app/main.py`:
   ```python
   from app.routers import my_feature
   application.include_router(my_feature.router, prefix=_settings.api_v1_prefix)
   ```
4. Add tests to `tests/test_my_feature.py`.
