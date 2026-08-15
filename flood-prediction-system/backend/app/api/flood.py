"""
Flood Detection API Endpoints
-----------------------------
REST API for flood detection and analysis.
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
import logging
import os
import uuid
from datetime import datetime

from app.schemas.flood import (
    FloodDetectionRequest,
    FloodDetectionResponse,
    HistoricalAnalysisRequest,
    HistoricalAnalysisResponse,
    FloodRiskRequest,
    FloodRiskResponse,
    JobStatusResponse
)
from app.services.job_manager import job_manager, ProcessingJob
from app.services.tasks import (
    process_satellite_data,
    run_historical_analysis,
    predict_flood_risk,
    analyze_flood_flow
)
from app.models import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/flood", tags=["Flood Detection"])


@router.post("/detect", response_model=FloodDetectionResponse)
async def detect_flood(request: FloodDetectionRequest, db: Session = Depends(get_db)):
    """
    Detect flood extent from satellite imagery.
    
    Supports both Sentinel-1 SAR and Sentinel-2 optical data.
    Queues async job for processing and returns job ID for status tracking.
    """
    job_id = str(uuid.uuid4())
    
    try:
        # Queue async task
        task = process_satellite_data.delay(
            aoi_geojson=request.aoi_geojson,
            start_date=datetime.now().isoformat(),
            end_date=datetime.now().isoformat(),
            satellite_source="sentinel1" if request.sensor_type == "sentinel-1" else "sentinel2",
            job_id=job_id
        )
        
        # Create initial job record
        job = ProcessingJob(
            job_id=job_id,
            job_type="flood_detection",
            status="QUEUED",
            request_data=request.dict()
        )
        job_manager.add_job(job)
        
        return FloodDetectionResponse(
            job_id=job_id,
            status="QUEUED",
            message="Flood detection job queued. Check status at /api/status/{job_id}"
        )
        
    except Exception as e:
        logger.error(f"Error queuing flood detection: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/historical", response_model=HistoricalAnalysisResponse)
async def analyze_historical_floods(request: HistoricalAnalysisRequest, db: Session = Depends(get_db)):
    """
    Analyze historical flood patterns for an AOI.
    
    Retrieves past satellite observations and calculates:
    - Historical water extent
    - Flood frequency
    - Maximum observed flood extent
    - Seasonal patterns
    """
    job_id = str(uuid.uuid4())
    
    try:
        # Queue async task
        task = run_historical_analysis.delay(
            aoi_geojson=request.aoi_geojson,
            start_date=request.start_date.isoformat(),
            end_date=request.end_date.isoformat(),
            job_id=job_id
        )
        
        # Create initial job record
        job = ProcessingJob(
            job_id=job_id,
            job_type="historical_analysis",
            status="QUEUED",
            request_data=request.dict()
        )
        job_manager.add_job(job)
        
        return HistoricalAnalysisResponse(
            job_id=job_id,
            status="QUEUED",
            message="Historical analysis job queued. Check status at /api/status/{job_id}"
        )
        
    except Exception as e:
        logger.error(f"Error queuing historical analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/predict", response_model=FloodRiskResponse)
async def predict_flood_risk(request: FloodRiskRequest, db: Session = Depends(get_db)):
    """
    Predict flood risk/susceptibility for an area.
    
    Uses terrain, historical data, and environmental factors
    to estimate flood susceptibility.
    """
    job_id = str(uuid.uuid4())
    
    try:
        # Queue async task
        task = predict_flood_risk.delay(
            aoi_geojson=request.aoi_geojson,
            recent_flood_geojson=None,  # Can be added from request
            job_id=job_id
        )
        
        # Create initial job record
        job = ProcessingJob(
            job_id=job_id,
            job_type="risk_prediction",
            status="QUEUED",
            request_data=request.dict()
        )
        job_manager.add_job(job)
        
        return FloodRiskResponse(
            job_id=job_id,
            status="QUEUED",
            message="Risk prediction job queued. Check status at /api/status/{job_id}"
        )
        
    except Exception as e:
        logger.error(f"Error queuing risk prediction: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/flow")
async def generate_flood_flow(request: FloodRiskRequest, db: Session = Depends(get_db)):
    """
    Generate flood flow/spread visualization.
    
    Creates flow direction arrows and potential spread areas
    based on terrain analysis.
    """
    job_id = str(uuid.uuid4())
    
    try:
        # Queue async task
        task = analyze_flood_flow.delay(
            aoi_geojson=request.aoi_geojson,
            flood_extent_geojson=None,
            job_id=job_id
        )
        
        # Create initial job record
        job = ProcessingJob(
            job_id=job_id,
            job_type="flow_analysis",
            status="QUEUED",
            request_data=request.dict()
        )
        job_manager.add_job(job)
        
        return {
            "job_id": job_id,
            "status": "QUEUED",
            "message": "Flow analysis job queued. Check status at /api/status/{job_id}"
        }
        
    except Exception as e:
        logger.error(f"Error queuing flow analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))
