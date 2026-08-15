"""
Flood Detection Module
----------------------
Algorithms and services for detecting floods from satellite imagery.
"""

from app.flood_detection.algorithms import (
    calculate_ndwi,
    calculate_mndwi,
    detect_flood_sar,
    detect_flood_optical,
    adaptive_threshold_otsu
)

__all__ = [
    # Algorithms
    "calculate_ndwi",
    "calculate_mndwi",
    "detect_flood_sar",
    "detect_flood_optical",
    "adaptive_threshold_otsu",
]
