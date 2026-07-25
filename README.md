# Autonomous Data Scientist

Autonomous Data Scientist is a FastAPI + React platform for dataset ingestion,
analysis, and multi-agent machine learning workflows.

## Tech Stack

- **Backend**: Python 3.12, FastAPI, SQLAlchemy, LangGraph, MLflow.
- **Frontend**: React, TypeScript, Vite.
- **Local data**: SQLite by default for local testing.
- **Observability / ML**: Prometheus metrics, MLflow, structured logging.

## Local Quickstart

### 1. Open Terminal in the Project Root
```bash
cd "/Users/esakkikannan/Autonomous Data Scientist"
```

### 2. Install Dependencies (Once)
```bash
make install
```

### 3. Start the Backend
In Terminal 1:
```bash
make backend
```

* **Backend runs at:** `http://127.0.0.1:8000`
* **API docs:** `http://127.0.0.1:8000/docs`

### 4. Start the Frontend
Open a second Terminal:
```bash
cd "/Users/esakkikannan/Autonomous Data Scientist"
make frontend
```

* **Frontend runs at:** `http://127.0.0.1:5173/`

### 5. Access the Application
Open this in your browser: [http://127.0.0.1:5173/](http://127.0.0.1:5173/)

### Quick Check
```bash
curl http://127.0.0.1:8000/health
```
**Expected response:**
```json
{"status":"ok"}
```

**Note:** Don't use `docker-compose.yml` now. Docker was removed for local-first testing.

## Useful Commands

```bash
make test
make lint
make type-check
```

Docker configuration has been removed for the current local-first phase. Once
the app is working locally, Docker can be added back as a deployment layer.
# Nova---AI
