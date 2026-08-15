"""
Export API Endpoints
---------------------
REST API for exporting flood analysis results in various formats.
"""

from fastapi import APIRouter, HTTPException, Response
from fastapi.responses import FileResponse, JSONResponse
from typing import Optional, Dict, Any
import logging
import os
import json
import io

from app.services.job_manager import job_manager
from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/export", tags=["Export"])


@router.get("/geojson/{job_id}")
async def export_geojson(job_id: str):
    """
    Export flood extent as GeoJSON.
    
    Returns the flood detection result as a GeoJSON file.
    """
    job = job_manager.get_job(job_id)
    
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    
    if job.status != "COMPLETED":
        raise HTTPException(status_code=400, detail="Job not completed yet")
    
    # Try to get GeoJSON from result
    if job.result and isinstance(job.result, dict):
        geojson_path = job.result.get("geojson_path") or job.result.get("risk_geojson_path") or job.result.get("flow_geojson_path")
        
        if geojson_path and os.path.exists(geojson_path):
            return FileResponse(
                path=geojson_path,
                media_type="application/geo+json",
                filename=f"flood_{job_id}.geojson"
            )
    
    # Generate GeoJSON from result data if available
    if job.result and "flooded_area_km2" in job.result:
        # Create simple GeoJSON feature
        geojson = {
            "type": "FeatureCollection",
            "features": [{
                "type": "Feature",
                "properties": {
                    "job_id": job_id,
                    "flooded_area_km2": job.result.get("flooded_area_km2", 0),
                    "detection_method": job.result.get("detection_method", "unknown")
                },
                "geometry": {
                    "type": "Polygon",
                    "coordinates": []  # Would need actual geometry
                }
            }]
        }
        
        return JSONResponse(
            content=geojson,
            media_type="application/geo+json",
            headers={"Content-Disposition": f"attachment; filename=flood_{job_id}.geojson"}
        )
    
    raise HTTPException(status_code=404, detail="No GeoJSON result available for this job")


@router.get("/geotiff/{job_id}")
async def export_geotiff(job_id: str):
    """
    Export flood raster as GeoTIFF.
    
    Returns the flood detection result as a Cloud-Optimized GeoTIFF.
    """
    job = job_manager.get_job(job_id)
    
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    
    if job.status != "COMPLETED":
        raise HTTPException(status_code=400, detail="Job not completed yet")
    
    # Check for GeoTIFF result
    if job.result and isinstance(job.result, dict):
        geotiff_path = job.result.get("geotiff_path") or job.result.get("risk_raster_path")
        
        if geotiff_path and os.path.exists(geotiff_path):
            return FileResponse(
                path=geotiff_path,
                media_type="image/tiff",
                filename=f"flood_{job_id}.tif"
            )
    
    raise HTTPException(status_code=404, detail="No GeoTIFF result available for this job")


@router.get("/statistics/{job_id}")
async def export_statistics(job_id: str):
    """
    Export analysis statistics as JSON.
    
    Returns comprehensive statistics about the flood analysis.
    """
    job = job_manager.get_job(job_id)
    
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    
    if job.status != "COMPLETED":
        raise HTTPException(status_code=400, detail="Job not completed yet")
    
    # Build statistics response
    stats = {
        "job_id": job_id,
        "job_type": job.job_type,
        "completed_at": job.completed_at.isoformat() if job.completed_at else None,
        "processing_time_seconds": None,
        "results": job.result or {}
    }
    
    if job.started_at and job.completed_at:
        stats["processing_time_seconds"] = (job.completed_at - job.started_at).total_seconds()
    
    return JSONResponse(
        content=stats,
        headers={"Content-Disposition": f"attachment; filename=statistics_{job_id}.json"}
    )


@router.get("/report/{job_id}")
async def generate_report(job_id: str, format: str = "json"):
    """
    Generate comprehensive analysis report.
    
    Args:
        job_id: Job ID
        format: Output format (json, md)
    """
    job = job_manager.get_job(job_id)
    
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    
    if job.status != "COMPLETED":
        raise HTTPException(status_code=400, detail="Job not completed yet")
    
    # Generate report
    report = {
        "title": "Flood Analysis Report",
        "job_id": job_id,
        "analysis_type": job.job_type,
        "created_at": job.created_at.isoformat(),
        "completed_at": job.completed_at.isoformat() if job.completed_at else None,
        "request_parameters": job.request_data,
        "results": job.result,
        "disclaimer": "This is a model-based estimate. Actual flood conditions may vary."
    }
    
    if format.lower() == "md":
        # Generate Markdown report
        md_content = f"""# Flood Analysis Report

## Job Information
- **Job ID**: {job_id}
- **Analysis Type**: {job.job_type}
- **Created**: {job.created_at.isoformat()}
- **Completed**: {job.completed_at.isoformat() if job.completed_at else 'N/A'}

## Results
{json.dumps(job.result, indent=2) if job.result else 'No results available'}

## Disclaimer
This is a model-based estimate using satellite imagery analysis. 
Actual flood conditions may vary due to local factors not captured in the analysis.
"""
        return Response(
            content=md_content,
            media_type="text/markdown",
            headers={"Content-Disposition": f"attachment; filename=report_{job_id}.md"}
        )
    
    return JSONResponse(
        content=report,
        headers={"Content-Disposition": f"attachment; filename=report_{job_id}.json"}
    )


@router.get("/shapefile/{job_id}")
async def export_shapefile(job_id: str):
    """
    Export flood extent as Shapefile (requires geopandas).
    
    Note: This endpoint requires additional processing to convert GeoJSON to Shapefile.
    """
    job = job_manager.get_job(job_id)
    
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    
    if job.status != "COMPLETED":
        raise HTTPException(status_code=400, detail="Job not completed yet")
    
    # Check if shapefile was generated during processing
    if job.result and isinstance(job.result, dict):
        shapefile_path = job.result.get("shapefile_path")
        
        if shapefile_path and os.path.exists(shapefile_path):
            # Shapefiles consist of multiple files (.shp, .shx, .dbf, .prj)
            # Return the main .shp file, others should be in same directory
            return FileResponse(
                path=shapefile_path,
                media_type="application/x-qgis-shapefile",
                filename=f"flood_{job_id}.shp"
            )
    
    raise HTTPException(
        status_code=404, 
        detail="Shapefile not available. Use GeoJSON export instead or request shapefile generation during processing."
    )


@router.post("/batch")
async def batch_export(job_ids: list[str], format: str = "geojson"):
    """
    Export multiple jobs in a single request.
    
    Args:
        job_ids: List of job IDs to export
        format: Export format (geojson, statistics)
    """
    results = {}
    errors = []
    
    for job_id in job_ids:
        try:
            job = job_manager.get_job(job_id)
            if job and job.status == "COMPLETED":
                results[job_id] = job.result
            else:
                errors.append({"job_id": job_id, "error": "Job not found or not completed"})
        except Exception as e:
            errors.append({"job_id": job_id, "error": str(e)})
    
    return {
        "format": format,
        "successful_exports": len(results),
        "failed_exports": len(errors),
        "results": results,
        "errors": errors
    }
