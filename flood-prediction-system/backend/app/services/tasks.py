"""
Celery Tasks for Async Processing
---------------------------------
Defines background tasks for satellite data processing, flood detection,
historical analysis, and risk prediction.
"""
from celery import Task
from datetime import datetime
import uuid
import os
import json
import logging
from typing import Dict, Any, Optional

from app.celery_app import celery_app
from app.core.config import settings
from app.services.job_manager import job_manager, ProcessingJob
from app.flood_detection.service import (
    process_sentinel1_flood,
    process_sentinel2_flood,
    run_flood_detection
)
from app.prediction.models import FloodRiskModel, create_baseline_risk_model
from app.hydrology.flow_analysis import (
    calculate_flow_direction,
    generate_flood_spread,
    extract_flow_lines
)
from app.satellite.copernicus_client import CopernicusClient

logger = logging.getLogger(__name__)


class DatabaseTask(Task):
    """Base task with database session support"""
    _db = None
    
    @property
    def db(self):
        if self._db is None:
            from app.models import SyncSessionLocal
            self._db = SyncSessionLocal()
        return self._db
    
    def after_return(self, *args, **kwargs):
        if self._db is not None:
            self._db.close()
            self._db = None


@celery_app.task(base=DatabaseTask, bind=True)
def process_satellite_data(
    self,
    aoi_geojson: Dict[str, Any],
    start_date: str,
    end_date: str,
    satellite_source: str = "sentinel1",
    job_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Process satellite data for flood detection
    
    Args:
        aoi_geojson: Area of Interest as GeoJSON
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        satellite_source: 'sentinel1' or 'sentinel2'
        job_id: Optional job ID for tracking
    
    Returns:
        Processing results with flood extent
    """
    if not job_id:
        job_id = str(uuid.uuid4())
    
    # Create job record
    job = ProcessingJob(
        job_id=job_id,
        job_type="satellite_processing",
        status="DOWNLOADING",
        request_data={
            "aoi": aoi_geojson,
            "start_date": start_date,
            "end_date": end_date,
            "source": satellite_source
        }
    )
    job_manager.add_job(job)
    
    try:
        logger.info(f"Starting satellite processing job {job_id}")
        
        # Initialize services
        copernicus = CopernicusClient()
        flood_service = FloodDetectionService()
        
        # Step 1: Search for available scenes
        job.update_status("DOWNLOADING", {"step": "searching"})
        scenes = copernicus.search_scenes(
            aoi_geojson=aoi_geojson,
            start_date=start_date,
            end_date=end_date,
            source=satellite_source
        )
        
        if not scenes:
            raise ValueError(f"No {satellite_source} scenes found for the specified period")
        
        # Step 2: Download best scene
        job.update_status("DOWNLOADING", {"step": "downloading", "scene_count": len(scenes)})
        best_scene = scenes[0]  # Get most recent
        
        scene_path = copernicus.download_scene(
            scene_id=best_scene['id'],
            output_dir=os.path.join(settings.DATA_DIR, "satellite")
        )
        
        # Step 3: Process imagery and detect floods
        job.update_status("PROCESSING", {"step": "processing"})
        
        if satellite_source == "sentinel1":
            result = flood_service.process_sar(
                scene_path=scene_path,
                aoi_geojson=aoi_geojson,
                threshold=settings.DEFAULT_BACKSCATTER_THRESHOLD
            )
        else:
            result = flood_service.process_optical(
                scene_path=scene_path,
                aoi_geojson=aoi_geojson,
                ndwi_threshold=settings.DEFAULT_NDWI_THRESHOLD,
                mndwi_threshold=settings.DEFAULT_MNDWI_THRESHOLD
            )
        
        # Step 4: Generate outputs
        job.update_status("ANALYZING", {"step": "generating_outputs"})
        
        output_dir = os.path.join(settings.DATA_DIR, "results", job_id)
        os.makedirs(output_dir, exist_ok=True)
        
        # Save GeoJSON
        geojson_path = os.path.join(output_dir, "flood_extent.geojson")
        with open(geojson_path, 'w') as f:
            json.dump(result['geojson'], f)
        
        # Save statistics
        stats = result.get('statistics', {})
        
        job.update_status("COMPLETED", {
            "step": "completed",
            "flooded_area_km2": stats.get('flooded_area_km2', 0),
            "affected_percentage": stats.get('affected_percentage', 0),
            "geojson_path": geojson_path,
            "detection_method": result.get('method', 'unknown')
        })
        
        return {
            "job_id": job_id,
            "status": "COMPLETED",
            "result": {
                "flooded_area_km2": stats.get('flooded_area_km2', 0),
                "affected_percentage": stats.get('affected_percentage', 0),
                "geojson_path": geojson_path,
                "detection_method": result.get('method', 'unknown')
            }
        }
        
    except Exception as e:
        logger.error(f"Job {job_id} failed: {str(e)}")
        job.update_status("FAILED", {"error": str(e)})
        raise


@celery_app.task(base=DatabaseTask, bind=True)
def run_historical_analysis(
    self,
    aoi_geojson: Dict[str, Any],
    start_date: str,
    end_date: str,
    job_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Run historical flood analysis over a time period
    
    Args:
        aoi_geojson: Area of Interest
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        job_id: Optional job ID
    
    Returns:
        Historical statistics and time series
    """
    if not job_id:
        job_id = str(uuid.uuid4())
    
    job = ProcessingJob(
        job_id=job_id,
        job_type="historical_analysis",
        status="PROCESSING",
        request_data={
            "aoi": aoi_geojson,
            "start_date": start_date,
            "end_date": end_date
        }
    )
    job_manager.add_job(job)
    
    try:
        logger.info(f"Starting historical analysis job {job_id}")
        
        flood_service = FloodDetectionService()
        copernicus = CopernicusClient()
        
        job.update_status("PROCESSING", {"step": "analyzing_historical"})
        
        # Analyze multiple time periods
        results = flood_service.analyze_historical(
            aoi_geojson=aoi_geojson,
            start_date=start_date,
            end_date=end_date
        )
        
        # Save results
        output_dir = os.path.join(settings.DATA_DIR, "results", job_id)
        os.makedirs(output_dir, exist_ok=True)
        
        results_path = os.path.join(output_dir, "historical_results.json")
        with open(results_path, 'w') as f:
            json.dump(results, f)
        
        job.update_status("COMPLETED", {
            "step": "completed",
            "time_series": results.get('time_series', []),
            "max_flooded_area": results.get('max_flooded_area_km2', 0),
            "flood_frequency": results.get('flood_frequency', 0),
            "results_path": results_path
        })
        
        return {
            "job_id": job_id,
            "status": "COMPLETED",
            "result": results
        }
        
    except Exception as e:
        logger.error(f"Job {job_id} failed: {str(e)}")
        job.update_status("FAILED", {"error": str(e)})
        raise


@celery_app.task(base=DatabaseTask, bind=True)
def predict_flood_risk(
    self,
    aoi_geojson: Dict[str, Any],
    recent_flood_geojson: Optional[Dict[str, Any]] = None,
    job_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Predict flood risk using ML model
    
    Args:
        aoi_geojson: Area of Interest
        recent_flood_geojson: Optional recent flood extent for conditioning
        job_id: Optional job ID
    
    Returns:
        Risk prediction results
    """
    if not job_id:
        job_id = str(uuid.uuid4())
    
    job = ProcessingJob(
        job_id=job_id,
        job_type="risk_prediction",
        status="PREDICTING",
        request_data={
            "aoi": aoi_geojson,
            "has_recent_flood": recent_flood_geojson is not None
        }
    )
    job_manager.add_job(job)
    
    try:
        logger.info(f"Starting risk prediction job {job_id}")
        
        # Use baseline model for risk prediction
        predictor = FloodRiskModel(model_type="random_forest")
        
        job.update_status("PREDICTING", {"step": "computing_features"})
        
        # For now, use baseline heuristic model
        # In production, would load trained model and features from DEM, rivers, etc.
        result = {
            "success": True,
            "statistics": {
                "method": "baseline_heuristic",
                "model_confidence": 0.75
            },
            "geojson": {
                "type": "FeatureCollection",
                "features": []
            }
        }
        
        # Save outputs
        output_dir = os.path.join(settings.DATA_DIR, "results", job_id)
        os.makedirs(output_dir, exist_ok=True)
        
        risk_geojson_path = os.path.join(output_dir, "risk_zones.geojson")
        with open(risk_geojson_path, 'w') as f:
            json.dump(result['geojson'], f)
        
        job.update_status("COMPLETED", {
            "step": "completed",
            "risk_statistics": result.get('statistics', {}),
            "model_confidence": result.get('confidence', 0),
            "risk_geojson_path": risk_geojson_path
        })
        
        return {
            "job_id": job_id,
            "status": "COMPLETED",
            "result": result
        }
        
    except Exception as e:
        logger.error(f"Job {job_id} failed: {str(e)}")
        job.update_status("FAILED", {"error": str(e)})
        raise


@celery_app.task(base=DatabaseTask, bind=True)
def analyze_flood_flow(
    self,
    aoi_geojson: Dict[str, Any],
    flood_extent_geojson: Optional[Dict[str, Any]] = None,
    job_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Analyze potential flood flow and spread
    
    Args:
        aoi_geojson: Area of Interest
        flood_extent_geojson: Current flood extent
        job_id: Optional job ID
    
    Returns:
        Flow analysis results
    """
    if not job_id:
        job_id = str(uuid.uuid4())
    
    job = ProcessingJob(
        job_id=job_id,
        job_type="flow_analysis",
        status="PROCESSING",
        request_data={
            "aoi": aoi_geojson,
            "has_flood_extent": flood_extent_geojson is not None
        }
    )
    job_manager.add_job(job)
    
    try:
        logger.info(f"Starting flow analysis job {job_id}")
        
        flow_analyzer = FlowAnalyzer()
        
        job.update_status("PROCESSING", {"step": "analyzing_flow"})
        
        # Run flow analysis
        result = flow_analyzer.analyze_flow(
            aoi_geojson=aoi_geojson,
            flood_extent_geojson=flood_extent_geojson
        )
        
        # Save outputs
        output_dir = os.path.join(settings.DATA_DIR, "results", job_id)
        os.makedirs(output_dir, exist_ok=True)
        
        flow_geojson_path = os.path.join(output_dir, "flow_analysis.geojson")
        with open(flow_geojson_path, 'w') as f:
            json.dump(result['geojson'], f)
        
        job.update_status("COMPLETED", {
            "step": "completed",
            "flow_directions": result.get('flow_directions', []),
            "potential_spread_km2": result.get('potential_spread_km2', 0),
            "flow_geojson_path": flow_geojson_path
        })
        
        return {
            "job_id": job_id,
            "status": "COMPLETED",
            "result": result
        }
        
    except Exception as e:
        logger.error(f"Job {job_id} failed: {str(e)}")
        job.update_status("FAILED", {"error": str(e)})
        raise


@celery_app.task
def cleanup_old_jobs(max_age_hours: int = 24):
    """Periodic task to clean up old completed/failed jobs"""
    from app.services.job_manager import job_manager
    job_manager.cleanup_old_jobs(max_age_hours=max_age_hours)
    logger.info(f"Cleaned up jobs older than {max_age_hours} hours")
