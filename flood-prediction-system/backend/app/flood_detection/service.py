"""
Flood Detection Service
-----------------------
Orchestrates satellite data processing and flood detection algorithms.
Handles raster I/O, reprojection, and result export.
"""

import os
import tempfile
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
import numpy as np
import rasterio
from rasterio.mask import mask
from rasterio.warp import calculate_default_transform, reproject, Resampling
from shapely.geometry import mapping, shape
import geopandas as gpd

from app.flood_detection.algorithms import (
    detect_flood_sar,
    detect_flood_optical,
    adaptive_threshold_otsu
)
from app.core.config import settings

logger = logging.getLogger(__name__)


def clip_raster_to_aoi(
    raster_path: str,
    aoi_geojson: Dict[str, Any],
    output_path: Optional[str] = None
) -> Tuple[np.ndarray, dict]:
    """
    Clip a raster file to an Area of Interest (AOI).
    
    Args:
        raster_path: Path to input GeoTIFF
        aoi_geojson: GeoJSON dictionary of AOI
        output_path: Optional path to save clipped raster
        
    Returns:
        Tuple of (clipped_data_array, metadata_dict)
    """
    try:
        with rasterio.open(raster_path) as src:
            # Convert AOI to proper geometry
            aoi_geom = shape(aoi_geojson)
            
            # Clip
            out_image, out_transform = mask(src, [aoi_geom], crop=True)
            out_meta = src.meta.copy()
            
            # Update metadata
            out_meta.update({
                "height": out_image.shape[1],
                "width": out_image.shape[2],
                "transform": out_transform
            })
            
            if output_path:
                with rasterio.open(output_path, 'w', **out_meta) as dest:
                    dest.write(out_image)
                logger.info(f"Clipped raster saved to {output_path}")
            
            return out_image, out_meta
            
    except Exception as e:
        logger.error(f"Error clipping raster: {e}")
        raise


def process_sentinel1_flood(
    pre_event_path: str,
    post_event_path: str,
    aoi_geojson: Dict[str, Any],
    polarization: str = "VV",
    threshold_db: float = -18.0,
    min_area_pixels: int = 50,
    output_dir: Optional[str] = None
) -> Dict[str, Any]:
    """
    Process Sentinel-1 SAR data for flood detection.
    
    Workflow:
    1. Load and clip pre/post event images to AOI
    2. Apply backscatter thresholding
    3. Generate flood mask
    4. Calculate statistics
    5. Export results
    
    Args:
        pre_event_path: Path to pre-event VV GeoTIFF
        post_event_path: Path to post-event VV GeoTIFF
        aoi_geojson: Area of Interest GeoJSON
        polarization: Polarization to use (VV or VH)
        threshold_db: Backscatter threshold in dB
        min_area_pixels: Minimum connected component size
        output_dir: Directory for output files
        
    Returns:
        Dictionary with masks, stats, and output paths
    """
    logger.info(f"Processing Sentinel-1 flood detection for AOI")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Clip rasters
        pre_clipped, pre_meta = clip_raster_to_aoi(pre_event_path, aoi_geojson)
        post_clipped, post_meta = clip_raster_to_aoi(post_event_path, aoi_geojson)
        
        # Ensure we have 2D arrays (single band)
        if len(pre_clipped.shape) == 3:
            pre_data = pre_clipped[0]
            post_data = post_clipped[0]
        else:
            pre_data = pre_clipped
            post_data = post_clipped
        
        # Run flood detection algorithm
        result = detect_flood_sar(
            pre_event_data=pre_data,
            post_event_data=post_data,
            nodata=pre_meta.get('nodata', -9999),
            min_area_pixels=min_area_pixels,
            permanent_water_threshold=threshold_db
        )
        
        # Prepare outputs
        flood_mask = result['flood_mask']
        water_mask = result['water_mask']
        stats = result['stats']
        
        # Update stats with geospatial info
        transform = post_meta['transform']
        pixel_size = abs(transform[0])  # Assuming square pixels
        pixel_area_m2 = pixel_size * pixel_size
        
        stats['pixel_size_m'] = pixel_size
        stats['flood_area_km2'] = (stats['flood_area_pixels'] * pixel_area_m2) / 1e6
        stats['water_area_km2'] = (stats['water_area_pixels'] * pixel_area_m2) / 1e6
        
        # Save results if output_dir provided
        output_paths = {}
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
            
            # Create GeoTIFF for flood mask
            flood_tiff = os.path.join(output_dir, "flood_mask.tif")
            meta_out = post_meta.copy()
            meta_out.update({
                'dtype': 'uint8',
                'count': 1,
                'nodata': 255,
                'compress': 'lzw'
            })
            
            with rasterio.open(flood_tiff, 'w', **meta_out) as dst:
                dst.write(flood_mask.astype(np.uint8), 1)
            output_paths['flood_mask'] = flood_tiff
            
            # Create GeoTIFF for water mask
            water_tiff = os.path.join(output_dir, "water_mask.tif")
            with rasterio.open(water_tiff, 'w', **meta_out) as dst:
                dst.write(water_mask.astype(np.uint8), 1)
            output_paths['water_mask'] = water_tiff
            
            # Create GeoJSON polygons
            flood_polygons = mask_to_geojson(flood_mask, post_meta['transform'])
            water_polygons = mask_to_geojson(water_mask, post_meta['transform'])
            
            flood_gpkg = os.path.join(output_dir, "flood_polygons.gpkg")
            water_gpkg = os.path.join(output_dir, "water_polygons.gpkg")
            
            if flood_polygons:
                gpd.GeoDataFrame(flood_polygons, geometry='geometry', crs="EPSG:4326").to_file(flood_gpkg, driver="GPKG")
                output_paths['flood_polygons'] = flood_gpkg
                
            if water_polygons:
                gpd.GeoDataFrame(water_polygons, geometry='geometry', crs="EPSG:4326").to_file(water_gpkg, driver="GPKG")
                output_paths['water_polygons'] = water_gpkg
        
        return {
            "success": True,
            "masks": {
                "flood": flood_mask.tolist(),
                "water": water_mask.tolist()
            },
            "stats": stats,
            "output_paths": output_paths,
            "metadata": {
                "sensor": "Sentinel-1",
                "polarization": polarization,
                "threshold_db": threshold_db,
                "crs": post_meta.get('crs', 'EPSG:4326')
            }
        }


def process_sentinel2_flood(
    image_path: str,
    aoi_geojson: Dict[str, Any],
    bands: Dict[str, int],
    use_mndwi: bool = True,
    threshold: float = 0.3,
    min_area_pixels: int = 50,
    output_dir: Optional[str] = None
) -> Dict[str, Any]:
    """
    Process Sentinel-2 optical data for flood detection.
    
    Workflow:
    1. Load required bands (Green, NIR, SWIR)
    2. Calculate NDWI/MNDWI
    3. Apply thresholding
    4. Generate water mask
    5. Calculate statistics
    
    Args:
        image_path: Path to multi-band Sentinel-2 GeoTIFF
        aoi_geojson: Area of Interest
        bands: Dictionary mapping band names to band indices {green: 3, nir: 8, swir: 11}
        use_mndwi: Use MNDWI if SWIR available
        threshold: Water index threshold
        min_area_pixels: Minimum connected component size
        output_dir: Output directory
        
    Returns:
        Dictionary with masks, index array, stats, and paths
    """
    logger.info(f"Processing Sentinel-2 flood detection")
    
    try:
        with rasterio.open(image_path) as src:
            # Read bands
            green_idx = bands.get('green', 3)
            nir_idx = bands.get('nir', 8)
            swir_idx = bands.get('swir', 11)
            
            green_band = src.read(green_idx)
            nir_band = src.read(nir_idx)
            swir_band = src.read(swir_idx) if swir_idx <= src.count else None
            
            # Get metadata
            meta = src.meta.copy()
            transform = src.transform
            crs = src.crs
            
        # Clip to AOI if needed (simplified - assuming already clipped or small AOI)
        # In production, would clip each band
        
        # Run optical flood detection
        result = detect_flood_optical(
            green_band=green_band,
            nir_band=nir_band,
            swir_band=swir_band,
            nodata=meta.get('nodata', 0),
            threshold=threshold,
            use_mndwi=use_mndwi and swir_band is not None,
            min_area_pixels=min_area_pixels
        )
        
        water_mask = result['water_mask']
        index_array = result['index_array']
        stats = result['stats']
        
        # Calculate area
        pixel_size = abs(transform.a)
        pixel_area_m2 = pixel_size * pixel_size
        stats['pixel_size_m'] = pixel_size
        stats['water_area_km2'] = (stats['water_area_pixels'] * pixel_area_m2) / 1e6
        
        # Save outputs
        output_paths = {}
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
            
            # Water mask GeoTIFF
            water_tiff = os.path.join(output_dir, "water_mask.tif")
            meta_out = meta.copy()
            meta_out.update({
                'dtype': 'uint8',
                'count': 1,
                'nodata': 255,
                'compress': 'lzm'
            })
            
            with rasterio.open(water_tiff, 'w', **meta_out) as dst:
                dst.write(water_mask.astype(np.uint8), 1)
            output_paths['water_mask'] = water_tiff
            
            # Index array GeoTIFF (float32)
            index_tiff = os.path.join(output_dir, f"{stats['method']}_index.tif")
            meta_out['dtype'] = 'float32'
            meta_out['nodata'] = -9999
            
            with rasterio.open(index_tiff, 'w', **meta_out) as dst:
                dst.write(index_array.astype(np.float32), 1)
            output_paths['index_array'] = index_tiff
            
            # Polygons
            water_polygons = mask_to_geojson(water_mask, transform)
            if water_polygons:
                water_gpkg = os.path.join(output_dir, "water_polygons.gpkg")
                gpd.GeoDataFrame(water_polygons, geometry='geometry', crs=str(crs)).to_file(water_gpkg, driver="GPKG")
                output_paths['water_polygons'] = water_gpkg
        
        return {
            "success": True,
            "masks": {
                "water": water_mask.tolist()
            },
            "index_array": index_array.tolist(),
            "stats": stats,
            "output_paths": output_paths,
            "metadata": {
                "sensor": "Sentinel-2",
                "method": stats['method'],
                "threshold": threshold,
                "crs": str(crs)
            }
        }
        
    except Exception as e:
        logger.error(f"Error processing Sentinel-2 data: {e}")
        return {
            "success": False,
            "error": str(e)
        }


def mask_to_geojson(mask: np.ndarray, transform: rasterio.transform.Affine) -> list:
    """
    Convert binary mask to GeoJSON polygons.
    
    Args:
        mask: 2D binary numpy array
        transform: Rasterio transform
        
    Returns:
        List of GeoJSON Feature dictionaries
    """
    from skimage.measure import find_contours
    
    # Find contours
    contours = find_contours(mask.astype(float), 0.5)
    
    features = []
    for contour in contours:
        # Convert pixel coordinates to geographic
        coords = []
        for point in contour:
            row, col = point
            x, y = rasterio.transform.xy(transform, row, col)
            coords.append([x, y])
        
        # Close the ring
        if coords and coords[0] != coords[-1]:
            coords.append(coords[0])
        
        if len(coords) >= 4:  # Valid polygon
            feature = {
                "type": "Feature",
                "properties": {"area_type": "flood" if np.mean(mask) > 0 else "water"},
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [coords]
                }
            }
            features.append(feature)
    
    return features


# Convenience function for API usage
async def run_flood_detection(
    pre_event_file: Optional[str],
    post_event_file: Optional[str],
    aoi_geojson: Dict[str, Any],
    sensor_type: str = "sentinel-1",
    bands: Optional[Dict[str, int]] = None,
    output_dir: Optional[str] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Unified flood detection runner.
    
    Routes to appropriate processing function based on sensor type.
    """
    if sensor_type.lower() == "sentinel-1":
        if not pre_event_file or not post_event_file:
            return {"success": False, "error": "Both pre and post event files required for SAR"}
        
        return process_sentinel1_flood(
            pre_event_path=pre_event_file,
            post_event_path=post_event_file,
            aoi_geojson=aoi_geojson,
            output_dir=output_dir,
            **kwargs
        )
    
    elif sensor_type.lower() == "sentinel-2":
        if not post_event_file:
            return {"success": False, "error": "Post event file required for Optical"}
        
        default_bands = {"green": 3, "nir": 8, "swir": 11}
        bands = bands or default_bands
        
        return process_sentinel2_flood(
            image_path=post_event_file,
            aoi_geojson=aoi_geojson,
            bands=bands,
            output_dir=output_dir,
            **kwargs
        )
    
    else:
        return {"success": False, "error": f"Unsupported sensor: {sensor_type}"}
