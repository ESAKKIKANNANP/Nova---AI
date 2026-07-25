# =============================================================================
# backend/worker.py
#
# ARQ Worker entrypoint and background task definitions.
# =============================================================================

import asyncio
import logging
from typing import Dict, Any
from arq import create_pool
from arq.connections import RedisSettings
from services.email_service import send_email

log = logging.getLogger(__name__)

# Note: In a real environment, pull from os.environ
redis_settings = RedisSettings(host='localhost', port=6379)

async def run_ml_pipeline_task(ctx: Dict[str, Any], session_id: str, user_email: str):
    """
    Background task to run the heavy LangGraph ML Pipeline.
    """
    log.info(f"[{session_id}] Starting background ML Pipeline...")
    
    # 1. Simulate heavy work and update progress in Redis
    # In reality, this would invoke the compiled LangGraph workflow.
    # ctx['job_id'] is automatically available in ARQ.
    
    await asyncio.sleep(2)
    # Note: ARQ doesn't have a native 'update_state' like Celery. 
    # To track progress, workers usually write to a Redis key manually.
    # We will simulate the heavy work here.
    log.info(f"[{session_id}] Progress: 50% - Training Models...")
    
    await asyncio.sleep(2)
    log.info(f"[{session_id}] Progress: 100% - Pipeline Complete.")
    
    # 2. Send Email Notification
    subject = f"Pipeline Complete: {session_id}"
    body = f"Your Autonomous Data Scientist pipeline ({session_id}) has finished successfully. Please log in to view the reports."
    await send_email(user_email, subject, body)
    
    return {"status": "success", "session_id": session_id}

async def generate_report_task(ctx: Dict[str, Any], session_id: str):
    """
    Background task to generate heavy PDF/DOCX reports.
    """
    log.info(f"[{session_id}] Generating reports in background...")
    await asyncio.sleep(3)
    return {"status": "success", "session_id": session_id, "files": ["report.pdf", "report.docx"]}

async def startup(ctx):
    """Lifecycle hook for worker startup."""
    log.info("ARQ Worker starting...")
    # Initialize DB connections or LangGraph graphs here if needed

async def shutdown(ctx):
    """Lifecycle hook for worker shutdown."""
    log.info("ARQ Worker shutting down...")

# ARQ Worker configuration class
class WorkerSettings:
    functions = [run_ml_pipeline_task, generate_report_task]
    redis_settings = redis_settings
    on_startup = startup
    on_shutdown = shutdown
    max_jobs = 10
    job_timeout = 3600 # Allow ML pipelines up to 1 hour
    
# Fast way to get a pool in FastAPI
async def get_redis_pool():
    return await create_pool(redis_settings)
