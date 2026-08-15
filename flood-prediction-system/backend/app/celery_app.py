"""
Celery configuration and task definitions for async processing
"""
from celery import Celery
from celery.schedules import crontab
import os

from app.core.config import settings

# Celery app configuration
celery_app = Celery(
    'flood_prediction',
    broker=settings.celery_broker_url,
    backend=settings.celery_broker_url,
    include=['app.services.tasks']
)

# Celery configuration
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 hour max per task
    task_soft_time_limit=3300,  # 55 minutes soft limit
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=50,
    
    # Retry settings
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    
    # Rate limiting
    worker_send_task_events=True,
    task_send_sent_event=True,
)

# Periodic tasks (optional)
celery_app.conf.beat_schedule = {
    'cleanup-old-jobs': {
        'task': 'app.services.tasks.cleanup_old_jobs',
        'schedule': crontab(hour=2, minute=0),  # Daily at 2 AM
    },
}


def get_celery_app():
    """Get the Celery application instance"""
    return celery_app
