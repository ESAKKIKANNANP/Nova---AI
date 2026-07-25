# =============================================================================
# backend/api/v1/endpoints/tasks.py
#
# FastAPI endpoints to enqueue background jobs and check status.
# =============================================================================

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from arq.jobs import Job
from worker import get_redis_pool

router = APIRouter()

class PipelineJobRequest(BaseModel):
    session_id: str
    user_email: str

@router.post("/start-pipeline")
async def start_pipeline(request: PipelineJobRequest):
    """
    Enqueues the heavy ML pipeline job to run in the background via ARQ/Redis.
    """
    try:
        redis = await get_redis_pool()
        # Enqueue the job. Returns an arq.Job instance
        job = await redis.enqueue_job("run_ml_pipeline_task", request.session_id, request.user_email)
        
        if not job:
            raise HTTPException(status_code=500, detail="Failed to enqueue job.")
            
        return {"message": "Job successfully enqueued.", "job_id": job.job_id}
    except Exception as e:
        # Gracefully handle Redis connection errors if Redis isn't running
        raise HTTPException(status_code=503, detail=f"Job Queue unavailable: {str(e)}")

@router.get("/{job_id}/status")
async def get_job_status(job_id: str):
    """
    Polls the status of an ARQ job.
    """
    try:
        redis = await get_redis_pool()
        job = Job(job_id, redis)
        status = await job.status()
        
        if status.value == "not_found":
            raise HTTPException(status_code=404, detail="Job not found.")
            
        # Try to get the result if it's complete
        result = None
        if status.value == "complete":
            # timeout=0 means return immediately or None if not ready
            try:
                info = await job.result_info()
                if info:
                    result = info.result
            except Exception:
                pass
                
        return {
            "job_id": job_id,
            "status": status.value, # e.g. queued, in_progress, complete
            "result": result
        }
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=503, detail=f"Job Queue unavailable: {str(e)}")
