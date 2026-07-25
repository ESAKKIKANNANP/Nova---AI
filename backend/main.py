# =============================================================================
# backend/main.py
#
# Main FastAPI application definition.
# =============================================================================

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator
from api.v1.router import api_router
from utils.logger import log


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create database tables on startup (for local SQLite dev)."""
    from db.session import sync_engine
    from models.base import Base
    # Import all models so they register on Base.metadata
    import models.user  # noqa: F401
    import models.project  # noqa: F401
    import models.dataset  # noqa: F401
    import models.pipeline_run  # noqa: F401
    import models.report  # noqa: F401
    import models.experiment  # noqa: F401
    import models.model_artifact  # noqa: F401
    import models.chat_history  # noqa: F401
    Base.metadata.create_all(bind=sync_engine)
    log.info("Database tables created/verified.")
    yield


app = FastAPI(
    title="Autonomous Data Scientist API",
    description="API for managing dataset ingestion, analysis, and multi-agent workflows.",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS - allow frontend dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    log.info("Request started", method=request.method, url=str(request.url))
    response = await call_next(request)
    log.info("Request completed", status_code=response.status_code)
    return response

app.include_router(api_router, prefix="/api/v1")

# Instrument Prometheus Metrics
Instrumentator().instrument(app).expose(app)

@app.get("/health", tags=["Health"])
async def health_check():
    """Basic health check endpoint."""
    return {"status": "ok"}

