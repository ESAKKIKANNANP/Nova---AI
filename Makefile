# =============================================================================
# Makefile - Autonomous Data Scientist local development
#
# Runs the app directly on the host for local testing.
# =============================================================================

.PHONY: help install backend frontend dev test lint type-check clean

BACKEND_DIR := backend
FRONTEND_DIR := frontend

help:
	@echo ""
	@echo "  Autonomous Data Scientist - Local Makefile"
	@echo "  =========================================="
	@echo ""
	@echo "  make install      Install backend and frontend dependencies"
	@echo "  make backend      Start FastAPI at http://localhost:8000"
	@echo "  make frontend     Start Vite at http://localhost:5173"
	@echo "  make dev          Show the two commands to run in separate terminals"
	@echo "  make test         Run backend tests"
	@echo "  make lint         Run backend lint checks"
	@echo "  make type-check   Run frontend TypeScript checks"
	@echo "  make clean        Remove local cache files"
	@echo ""

install:
	cd $(BACKEND_DIR) && uv sync
	cd $(FRONTEND_DIR) && npm install

backend:
	cd $(BACKEND_DIR) && env ENV=development DEBUG=true DATABASE_URL=sqlite:///./dev.db ASYNC_DATABASE_URL=sqlite+aiosqlite:///./dev.db uv run uvicorn main:app --host 127.0.0.1 --port 8000

frontend:
	cd $(FRONTEND_DIR) && npm run dev -- --host 127.0.0.1

dev:
	@echo "Run these in two terminals:"
	@echo "  make backend"
	@echo "  make frontend"

test:
	cd $(BACKEND_DIR) && env ENV=development DEBUG=true DATABASE_URL=sqlite:///./test.db ASYNC_DATABASE_URL=sqlite+aiosqlite:///./test.db CHECKPOINTER_BACKEND=memory uv run pytest

lint:
	cd $(BACKEND_DIR) && uv run ruff check .

type-check:
	cd $(FRONTEND_DIR) && npm run type-check

clean:
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
	find . -type d -name .pytest_cache -prune -exec rm -rf {} +
	find . -type d -name .ruff_cache -prune -exec rm -rf {} +
