"""
Job Manager Service
-------------------
Manages background processing jobs for flood detection and analysis.
Provides job tracking, status updates, and result storage.
"""

import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
from threading import Lock

logger = logging.getLogger(__name__)


class ProcessingJob:
    """Represents a background processing job."""
    
    def __init__(
        self,
        job_id: str,
        job_type: str,
        status: str = "QUEUED",
        request_data: Optional[Dict[str, Any]] = None
    ):
        self.job_id = job_id
        self.job_type = job_type
        self.status = status
        self.progress = 0
        self.request_data = request_data or {}
        self.result: Optional[Dict[str, Any]] = None
        self.error: Optional[str] = None
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        self._lock = Lock()
    
    def update_status(self, new_status: str, data: Optional[Dict[str, Any]] = None):
        """Update job status with thread safety."""
        with self._lock:
            self.status = new_status
            self.updated_at = datetime.utcnow()
            
            if new_status == "COMPLETED" and data:
                self.result = data
                self.progress = 100
            elif new_status == "FAILED" and data:
                self.error = data.get("error", "Unknown error")
            elif data and "step" in data:
                # Update progress based on step
                self.progress = self._calculate_progress(data.get("step", ""))
    
    def _calculate_progress(self, step: str) -> int:
        """Calculate progress percentage based on current step."""
        progress_map = {
            "QUEUED": 0,
            "DOWNLOADING": 20,
            "PROCESSING": 40,
            "ANALYZING": 60,
            "PREDICTING": 80,
            "COMPLETED": 100
        }
        return progress_map.get(step.upper(), self.progress)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert job to dictionary for API response."""
        return {
            "job_id": self.job_id,
            "job_type": self.job_type,
            "status": self.status,
            "progress": self.progress,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "result": self.result,
            "error": self.error
        }


class JobManager:
    """Singleton manager for processing jobs."""
    
    _instance: Optional['JobManager'] = None
    _jobs: Dict[str, ProcessingJob] = {}
    _lock = Lock()
    
    def __new__(cls) -> 'JobManager':
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def add_job(self, job: ProcessingJob):
        """Add a new job to the manager."""
        with self._lock:
            self._jobs[job.job_id] = job
        logger.info(f"Job {job.job_id} ({job.job_type}) added to queue")
    
    def get_job(self, job_id: str) -> Optional[ProcessingJob]:
        """Get a job by ID."""
        return self._jobs.get(job_id)
    
    def update_job(self, job_id: str, status: str, data: Optional[Dict[str, Any]] = None):
        """Update an existing job's status."""
        job = self.get_job(job_id)
        if job:
            job.update_status(status, data)
            logger.debug(f"Job {job_id} updated to {status}")
        else:
            logger.warning(f"Job {job_id} not found for update")
    
    def get_all_jobs(self, limit: int = 100) -> List[ProcessingJob]:
        """Get all jobs, sorted by creation time (newest first)."""
        jobs = sorted(
            self._jobs.values(),
            key=lambda j: j.created_at,
            reverse=True
        )
        return jobs[:limit]
    
    def get_active_jobs(self) -> List[ProcessingJob]:
        """Get all non-completed jobs."""
        return [
            j for j in self._jobs.values()
            if j.status not in ["COMPLETED", "FAILED"]
        ]
    
    def cleanup_old_jobs(self, max_age_hours: int = 24):
        """Remove completed/failed jobs older than specified hours."""
        cutoff = datetime.utcnow()
        from datetime import timedelta
        cutoff = cutoff - timedelta(hours=max_age_hours)
        
        with self._lock:
            to_remove = [
                job_id for job_id, job in self._jobs.items()
                if job.status in ["COMPLETED", "FAILED"]
                and job.updated_at < cutoff
            ]
            
            for job_id in to_remove:
                del self._jobs[job_id]
            
            if to_remove:
                logger.info(f"Cleaned up {len(to_remove)} old jobs")


# Global singleton instance
job_manager = JobManager()
