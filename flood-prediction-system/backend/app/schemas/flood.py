"""
Pydantic Schemas for Flood Detection API
-----------------------------------------
Request and response models for flood-related endpoints.
"""

from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
from datetime import datetime


class FloodDetectionRequest(BaseModel):
    """Request model for flood detection."""
    aoi_geojson: Dict[str, Any] = Field(..., description="Area of Interest as GeoJSON")
    sensor_type: str = Field(default="sentinel-1", description="Sensor type: sentinel-1 or sentinel-2")
    pre_event_file: Optional[str] = Field(None, description="Path to pre-event image (required for SAR)")
    post_event_file: Optional[str] = Field(None, description="Path to post-event image")
    bands: Optional[Dict[str, int]] = Field(None, description="Band mapping for optical data")
    
    # SAR parameters
    threshold_db: float = Field(default=-18.0, description="Backscatter threshold in dB")
    
    # Optical parameters
    threshold: float = Field(default=0.3, description="Water index threshold")
    
    # Processing parameters
    min_area_pixels: int = Field(default=50, description="Minimum connected component size")
    
    class Config:
        schema_extra = {
            "example": {
                "aoi_geojson": {
                    "type": "Polygon",
                    "coordinates": [[[77.0, 28.0], [77.5, 28.0], [77.5, 28.5], [77.0, 28.5], [77.0, 28.0]]]
                },
                "sensor_type": "sentinel-1",
                "pre_event_file": "/app/data/satellite/pre_event.tif",
                "post_event_file": "/app/data/satellite/post_event.tif",
                "threshold_db": -18.0,
                "min_area_pixels": 50
            }
        }


class FloodDetectionResponse(BaseModel):
    """Response model for flood detection."""
    job_id: str
    status: str
    stats: Optional[Dict[str, Any]] = None
    output_paths: Optional[Dict[str, str]] = None
    metadata: Optional[Dict[str, Any]] = None
    message: Optional[str] = None


class HistoricalAnalysisRequest(BaseModel):
    """Request model for historical flood analysis."""
    aoi_geojson: Dict[str, Any] = Field(..., description="Area of Interest as GeoJSON")
    start_date: datetime = Field(..., description="Start date for analysis period")
    end_date: datetime = Field(..., description="End date for analysis period")
    sensor_type: str = Field(default="sentinel-1", description="Sensor type")
    limit: int = Field(default=50, description="Maximum number of scenes to analyze")


class HistoricalAnalysisResponse(BaseModel):
    """Response model for historical analysis."""
    job_id: str
    status: str
    historical_results: Optional[List[Dict[str, Any]]] = None
    statistics: Optional[Dict[str, Any]] = None
    message: Optional[str] = None


class FloodRiskRequest(BaseModel):
    """Request model for flood risk prediction."""
    aoi_geojson: Dict[str, Any] = Field(..., description="Area of Interest as GeoJSON")
    historical_flood_mask: Optional[List[List[int]]] = Field(None, description="Historical flood mask as 2D array")
    dem_file: Optional[str] = Field(None, description="Path to DEM file")
    river_network: Optional[Dict[str, Any]] = Field(None, description="River network GeoJSON")
    model_type: str = Field(default="baseline", description="Model type: baseline, random_forest, gradient_boosting")


class FloodRiskResponse(BaseModel):
    """Response model for flood risk prediction."""
    job_id: str
    status: str
    risk_score: Optional[List[List[float]]] = None
    risk_class: Optional[List[List[int]]] = None
    statistics: Optional[Dict[str, Any]] = None
    method: Optional[str] = None
    message: Optional[str] = None


class JobStatusResponse(BaseModel):
    """Response model for job status check."""
    job_id: str
    job_type: str
    status: str
    progress: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
