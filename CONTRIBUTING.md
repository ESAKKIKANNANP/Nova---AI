# Contributing to Autonomous Data Scientist

First off, thank you for considering contributing to the Autonomous Data Scientist! It's people like you that make open-source platforms great.

## Development Setup
1. We use `uv` for lightning-fast Python package management. Install it via `curl -LsSf https://astral.sh/uv/install.sh | sh`.
2. Navigate to `backend/` and run `uv sync`.
3. For the frontend, navigate to `frontend/` and run `npm install`.

## Pull Request Process
1. Ensure your code passes all linting (`flake8`, `black`, `eslint`).
2. Update the README.md with details of changes to the interface, if applicable.
3. Your PR will trigger our GitHub Actions CI pipeline. It must pass the `pytest` suite and `Trivy` security scans before merging.
4. You may merge the Pull Request in once you have the sign-off of at least one other developer.

## Branching Strategy
We use Trunk Based Development. Branch off `main` for your features, keep branches short-lived, and merge back to `main` via PR.
