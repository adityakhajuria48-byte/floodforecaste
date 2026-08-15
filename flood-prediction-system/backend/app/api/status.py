"""
Job Status API Endpoints
-------------------------
REST API for checking job status and retrieving results.
"""

from fastapi import APIRouter, HTTPException
from typing import Optional, Dict, Any
import logging

from app.services.job_manager import job_manager
from app.schemas.flood import JobStatusResponse

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Job Status"])


@router.get("/status/{job_id}", response_model=JobStatusResponse)
async def get_job_status(job_id: str):
    """
    Get the status of a processing job by ID.
    
    Returns current job status, progress, and results if completed.
    """
    job = job_manager.get_job(job_id)
    
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    
    return JobStatusResponse(
        job_id=job.job_id,
        job_type=job.job_type,
        status=job.status,
        progress=job.progress,
        created_at=job.created_at,
        updated_at=job.updated_at,
        result=job.result,
        error=job.error
    )


@router.get("/status")
async def list_jobs(status: Optional[str] = None, limit: int = 50):
    """
    List all jobs with optional status filter.
    
    Args:
        status: Filter by status (QUEUED, PROCESSING, COMPLETED, FAILED)
        limit: Maximum number of jobs to return
    """
    if status:
        # Filter by status
        all_jobs = [j for j in job_manager.get_all_jobs(limit=limit*2) if j.status == status.upper()]
        jobs = all_jobs[:limit]
    else:
        jobs = job_manager.get_all_jobs(limit=limit)
    
    return {
        "jobs": [job.to_dict() for job in jobs],
        "total": len(jobs),
        "active_count": len(job_manager.get_active_jobs())
    }


@router.delete("/status/{job_id}")
async def cancel_job(job_id: str):
    """
    Cancel a queued or running job.
    
    Note: Only works for jobs that haven't completed yet.
    """
    job = job_manager.get_job(job_id)
    
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    
    if job.status in ["COMPLETED", "FAILED"]:
        raise HTTPException(status_code=400, detail="Cannot cancel completed/failed jobs")
    
    # Update status to failed with cancellation message
    job.update_status("FAILED", {"error": "Job cancelled by user"})
    
    return {"message": f"Job {job_id} cancelled successfully"}


@router.get("/health")
async def health_check():
    """
    Health check endpoint for the job manager service.
    """
    active_jobs = job_manager.get_active_jobs()
    
    return {
        "status": "healthy",
        "active_jobs": len(active_jobs),
        "job_types": list(set(j.job_type for j in active_jobs))
    }
