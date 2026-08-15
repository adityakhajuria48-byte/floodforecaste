"""
Test Flood Detection Algorithms
-------------------------------
Unit tests for flood detection and prediction modules.
"""

import numpy as np
import pytest
from app.flood_detection.algorithms import (
    calculate_ndwi,
    calculate_mndwi,
    detect_flood_sar,
    detect_flood_optical,
    adaptive_threshold_otsu
)
from app.prediction.models import (
    create_baseline_risk_model,
    calculate_slope,
    calculate_distance_to_river
)
from app.hydrology.flow_analysis import (
    calculate_flow_direction,
    generate_flood_spread
)


def test_calculate_ndwi():
    """Test NDWI calculation."""
    # Create sample bands
    green = np.array([[100, 50, 200], [150, 80, 180]], dtype=float)
    nir = np.array([[50, 200, 30], [60, 190, 40]], dtype=float)
    
    ndwi = calculate_ndwi(nir, green)
    
    # Water should have high NDWI (> 0.3)
    # Vegetation should have low/negative NDWI
    assert ndwi.shape == green.shape
    assert -1 <= ndwi.min() <= 1
    assert -1 <= ndwi.max() <= 1
    
    # First pixel: (100-50)/(100+50) = 0.333 (water-like)
    expected_first = (100 - 50) / (100 + 50)
    assert abs(ndwi[0, 0] - expected_first) < 0.01


def test_calculate_mndwi():
    """Test MNDWI calculation."""
    green = np.array([[100, 50, 200], [150, 80, 180]], dtype=float)
    swir = np.array([[30, 200, 50], [40, 190, 60]], dtype=float)
    
    mndwi = calculate_mndwi(swir, green)
    
    assert mndwi.shape == green.shape
    assert -1 <= mndwi.min() <= 1
    assert -1 <= mndwi.max() <= 1


def test_detect_flood_sar():
    """Test SAR flood detection."""
    # Create synthetic SAR data
    # Pre-event: mostly dry land (higher backscatter)
    pre_event = np.full((50, 50), -10.0)  # dB - dry land
    pre_event[20:30, 20:30] = -22.0  # Permanent water
    
    # Post-event: flooded area (low backscatter)
    post_event = np.full((50, 50), -10.0)  # dB - dry land
    post_event[20:30, 20:30] = -22.0  # Permanent water (same)
    post_event[35:45, 35:45] = -22.0  # New flood area
    
    result = detect_flood_sar(
        pre_event_data=pre_event,
        post_event_data=post_event,
        permanent_water_threshold=-18.0,
        min_area_pixels=10
    )
    
    assert "flood_mask" in result or "stats" in result
    
    if "stats" in result:
        stats = result["stats"]
        assert "flood_area_pixels" in stats
        assert stats["flood_area_pixels"] > 0  # Should detect the new flood


def test_detect_flood_optical():
    """Test optical flood detection."""
    # Create sample bands
    green = np.full((50, 50), 100, dtype=float)
    nir = np.full((50, 50), 200, dtype=float)  # Vegetation
    swir = np.full((50, 50), 50, dtype=float)
    
    # Add water area (high green, low NIR/SWIR)
    green[20:30, 20:30] = 150
    nir[20:30, 20:30] = 30
    swir[20:30, 20:30] = 20
    
    result = detect_flood_optical(
        green_band=green,
        nir_band=nir,
        swir_band=swir,
        threshold=0.3,
        use_mndwi=True
    )
    
    assert "water_mask" in result
    assert "stats" in result
    
    water_mask = result["water_mask"]
    assert water_mask.shape == green.shape
    assert np.sum(water_mask) > 0  # Should detect water


def test_adaptive_threshold_otsu():
    """Test Otsu thresholding."""
    # Create bimodal distribution (land + water)
    data = np.concatenate([
        np.random.normal(-10, 2, 1000),  # Land
        np.random.normal(-22, 2, 1000)   # Water
    ])
    
    threshold = adaptive_threshold_otsu(data)
    
    # Threshold should be between the two modes
    assert -20 < threshold < -12


def test_calculate_slope():
    """Test slope calculation from DEM."""
    # Create simple ramp DEM
    dem = np.tile(np.arange(0, 100), (100, 1))
    
    slope = calculate_slope(dem, pixel_size=10.0)
    
    assert slope.shape == dem.shape
    # Slope should be constant for uniform ramp
    assert np.allclose(slope[1:-1, 1:-1], slope[10, 10], rtol=0.1)


def test_calculate_distance_to_river():
    """Test distance to river calculation."""
    # Create river mask (vertical line)
    river_mask = np.zeros((50, 50), dtype=bool)
    river_mask[:, 25] = True  # River in middle column
    
    distance = calculate_distance_to_river(river_mask, pixel_size=10.0)
    
    assert distance.shape == river_mask.shape
    # Distance at river should be 0
    assert distance[25, 25] == 0
    # Distance increases away from river
    assert distance[25, 0] > distance[25, 25]
    assert distance[25, 49] > distance[25, 25]


def test_create_baseline_risk_model():
    """Test baseline risk model creation."""
    # Create sample terrain data
    elevation = np.random.uniform(0, 100, (50, 50))
    slope = np.random.uniform(0, 30, (50, 50))
    distance_to_river = np.random.uniform(0, 1000, (50, 50))
    
    result = create_baseline_risk_model(
        elevation=elevation,
        slope=slope,
        distance_to_river=distance_to_river
    )
    
    assert "risk_score" in result
    assert "risk_class" in result
    assert "stats" in result
    
    risk_score = result["risk_score"]
    assert risk_score.shape == elevation.shape
    assert 0 <= risk_score.min() <= 1
    assert 0 <= risk_score.max() <= 1
    
    stats = result["stats"]
    assert "mean_risk_score" in stats
    assert "method" in stats
    assert stats["method"] == "heuristic_baseline"


def test_calculate_flow_direction():
    """Test flow direction calculation."""
    # Create simple DEM with clear flow direction
    dem = np.array([
        [100, 90, 80],
        [95, 85, 75],
        [90, 80, 70]
    ], dtype=float)
    
    flow_dir = calculate_flow_direction(dem)
    
    assert flow_dir.shape == dem.shape
    # Center cell should flow southeast (direction 7)
    assert flow_dir[1, 1] == 7


def test_generate_flood_spread():
    """Test flood spread generation."""
    # Create sample data
    flood_mask = np.zeros((50, 50), dtype=np.uint8)
    flood_mask[20:30, 20:30] = 1  # Initial flood
    
    dem = np.random.uniform(0, 50, (50, 50))
    # Make area around flood lower to allow spread
    dem[15:35, 15:35] = np.minimum(dem[15:35, 15:35], 25)
    
    result = generate_flood_spread(
        flood_mask=flood_mask,
        dem=dem,
        max_distance_meters=100.0,
        pixel_size=10.0
    )
    
    assert "spread_mask" in result
    assert "probability" in result
    assert "stats" in result
    
    spread_mask = result["spread_mask"]
    assert spread_mask.shape == flood_mask.shape
    assert np.sum(spread_mask) >= np.sum(flood_mask)  # Spread >= original


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
