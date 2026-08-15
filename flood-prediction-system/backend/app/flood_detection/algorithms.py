"""
Flood Detection Algorithms
--------------------------
Implements SAR (Sentinel-1) and Optical (Sentinel-2) flood detection methods.
"""

import numpy as np
from scipy import ndimage
from skimage.filters import threshold_otsu
from typing import Tuple, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


def calculate_ndwi(nir_band: np.ndarray, green_band: np.ndarray, nodata: float = -9999) -> np.ndarray:
    """
    Calculate Normalized Difference Water Index (NDWI).
    NDWI = (Green - NIR) / (Green + NIR)
    
    Values > 0.3 typically indicate water.
    """
    with np.errstate(divide='ignore', invalid='ignore'):
        denominator = green_band.astype(float) + nir_band.astype(float)
        ndwi = np.where(denominator == 0, -1, (green_band.astype(float) - nir_band.astype(float)) / denominator)
    
    # Handle nodata
    mask = (nir_band == nodata) | (green_band == nodata)
    ndwi[mask] = nodata
    
    return ndwi


def calculate_mndwi(swir_band: np.ndarray, green_band: np.ndarray, nodata: float = -9999) -> np.ndarray:
    """
    Calculate Modified Normalized Difference Water Index (MNDWI).
    MNDWI = (Green - SWIR) / (Green + SWIR)
    
    Better at suppressing built-up land noise than NDWI.
    """
    with np.errstate(divide='ignore', invalid='ignore'):
        denominator = green_band.astype(float) + swir_band.astype(float)
        mndwi = np.where(denominator == 0, -1, (green_band.astype(float) - swir_band.astype(float)) / denominator)
    
    mask = (swir_band == nodata) | (green_band == nodata)
    mndwi[mask] = nodata
    
    return mndwi


def detect_flood_sar(
    pre_event_data: np.ndarray,
    post_event_data: np.ndarray,
    nodata: float = -9999,
    min_area_pixels: int = 50,
    permanent_water_threshold: float = -18.0  # dB
) -> Dict[str, Any]:
    """
    Detect flood extent using Sentinel-1 SAR data.
    
    Methodology:
    1. Identify permanent water in pre-event image (low backscatter).
    2. Identify water in post-event image.
    3. Flood = Post-event water MINUS Pre-event water.
    
    Args:
        pre_event_data: VV polarization array (dB) for pre-flood
        post_event_data: VV polarization array (dB) for post-flood
        nodata: No-data value
        min_area_pixels: Minimum connected component size to remove noise
        permanent_water_threshold: Backscatter threshold for permanent water (default -18dB)
        
    Returns:
        Dictionary containing flood_mask, water_mask, stats
    """
    logger.info("Starting SAR flood detection...")
    
    # Create masks
    # Water typically has very low backscatter (< -18dB to -20dB depending on surface roughness)
    pre_water_mask = pre_event_data < permanent_water_threshold
    post_water_mask = post_event_data < permanent_water_threshold
    
    # Handle nodata
    valid_pre = pre_event_data != nodata
    valid_post = post_event_data != nodata
    
    pre_water_mask = pre_water_mask & valid_pre
    post_water_mask = post_water_mask & valid_post
    
    # Morphological cleaning (remove small noise)
    structure = ndimage.generate_binary_structure(2, 2)
    
    def clean_mask(mask):
        cleaned = ndimage.binary_opening(mask, structure=structure, iterations=1)
        labeled, n_features = ndimage.label(cleaned)
        component_sizes = np.bincount(labeled.ravel())
        # Keep only components larger than min_area_pixels
        small_components = np.where(component_sizes <= min_area_pixels)[0]
        mask_clean = np.isin(labeled, small_components, invert=True)
        return mask_clean & (labeled > 0)
    
    pre_water_clean = clean_mask(pre_water_mask)
    post_water_clean = clean_mask(post_water_mask)
    
    # Flood Detection: New water bodies
    # Flood = Post Water AND (NOT Pre Water)
    flood_mask = post_water_clean & (~pre_water_clean)
    
    # Clean flood mask specifically
    flood_mask = clean_mask(flood_mask)
    
    # Calculate statistics
    total_pixels = np.count_nonzero(valid_post)
    water_pixels = np.count_nonzero(post_water_clean)
    flood_pixels = np.count_nonzero(flood_mask)
    
    stats = {
        "total_valid_pixels": int(total_pixels),
        "water_area_pixels": int(water_pixels),
        "flood_area_pixels": int(flood_pixels),
        "method": "SAR_Backscatter_Thresholding",
        "threshold_db": permanent_water_threshold
    }
    
    return {
        "flood_mask": flood_mask.astype(np.uint8),
        "water_mask": post_water_clean.astype(np.uint8),
        "permanent_water_mask": pre_water_clean.astype(np.uint8),
        "stats": stats
    }


def detect_flood_optical(
    green_band: np.ndarray,
    nir_band: np.ndarray,
    swir_band: Optional[np.ndarray] = None,
    nodata: float = -9999,
    threshold: float = 0.3,
    use_mndwi: bool = True,
    min_area_pixels: int = 50
) -> Dict[str, Any]:
    """
    Detect flood extent using Sentinel-2 Optical data.
    
    Methodology:
    1. Calculate NDWI or MNDWI.
    2. Apply threshold to identify water.
    3. Clean noise.
    
    Args:
        green_band: Green band array
        nir_band: NIR band array
        swir_band: SWIR band array (required for MNDWI)
        nodata: No-data value
        threshold: Index threshold for water (default 0.3)
        use_mndwi: Use MNDWI if SWIR is available, else NDWI
        
    Returns:
        Dictionary containing water_mask, index_array, stats
    """
    logger.info("Starting Optical flood detection...")
    
    # Calculate Index
    if use_mndwi and swir_band is not None:
        index_array = calculate_mndwi(swir_band, green_band, nodata)
        index_name = "MNDWI"
    else:
        index_array = calculate_ndwi(nir_band, green_band, nodata)
        index_name = "NDWI"
    
    # Thresholding
    water_mask = index_array > threshold
    
    # Handle nodata
    valid_mask = index_array != nodata
    water_mask = water_mask & valid_mask
    
    # Morphological cleaning
    structure = ndimage.generate_binary_structure(2, 2)
    cleaned = ndimage.binary_opening(water_mask, structure=structure, iterations=1)
    
    labeled, n_features = ndimage.label(cleaned)
    component_sizes = np.bincount(labeled.ravel())
    small_components = np.where(component_sizes <= min_area_pixels)[0]
    final_mask = np.isin(labeled, small_components, invert=True)
    final_mask = final_mask & (labeled > 0)
    
    water_pixels = np.count_nonzero(final_mask)
    
    stats = {
        "water_area_pixels": int(water_pixels),
        "method": f"Optical_{index_name}",
        "threshold": threshold,
        "mean_index_value": float(np.mean(index_array[final_mask])) if water_pixels > 0 else 0.0
    }
    
    return {
        "water_mask": final_mask.astype(np.uint8),
        "index_array": index_array,
        "stats": stats
    }


def adaptive_threshold_otsu(data: np.ndarray, nodata: float = -9999) -> float:
    """
    Calculate optimal threshold using Otsu's method for bimodal histograms.
    Useful when no fixed threshold is known.
    """
    valid_data = data[data != nodata]
    
    if len(valid_data) < 100:
        # Not enough data for histogram, return default
        return -18.0
        
    try:
        threshold = threshold_otsu(valid_data)
        return float(threshold)
    except Exception as e:
        logger.warning(f"Otsu thresholding failed: {e}, using default")
        return -18.0
