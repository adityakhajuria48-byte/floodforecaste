"""
Flood Flow and Spread Visualization
------------------------------------
Generates flood flow direction and potential spread visualization.
Uses terrain analysis and hydrological concepts.
"""

import numpy as np
from typing import Dict, Any, Optional, Tuple, List
from scipy.ndimage import distance_transform_edt
import logging

logger = logging.getLogger(__name__)


def calculate_flow_direction(dem: np.ndarray, nodata: float = -9999) -> np.ndarray:
    """
    Calculate flow direction using D8 algorithm.
    
    Each cell flows to its steepest downslope neighbor.
    
    Direction encoding (D8):
        3 | 2 | 1
       ---------
        4 | x | 0
       ---------
        5 | 6 | 7
    
    Args:
        dem: Digital Elevation Model array
        nodata: No-data value
        
    Returns:
        Flow direction array with D8 encoding
    """
    rows, cols = dem.shape
    flow_dir = np.zeros_like(dem, dtype=np.int8)
    
    # Neighbor offsets (row, col) and direction codes
    neighbors = [
        (0, 1, 0),   # East
        (-1, 1, 1),  # Northeast
        (-1, 0, 2),  # North
        (-1, -1, 3), # Northwest
        (0, -1, 4),  # West
        (1, -1, 5),  # Southwest
        (1, 0, 6),   # South
        (1, 1, 7)    # Southeast
    ]
    
    valid_mask = dem != nodata
    
    for i in range(1, rows - 1):
        for j in range(1, cols - 1):
            if not valid_mask[i, j]:
                flow_dir[i, j] = -1  # Nodata
                continue
            
            center_elev = dem[i, j]
            max_slope = -np.inf
            flow_direction = -1
            
            for di, dj, direction in neighbors:
                ni, nj = i + di, j + dj
                if valid_mask[ni, nj]:
                    neighbor_elev = dem[ni, nj]
                    # Calculate slope (elevation difference)
                    slope = center_elev - neighbor_elev
                    
                    if slope > max_slope:
                        max_slope = slope
                        flow_direction = direction
            
            # If no downslope neighbor, mark as sink
            if max_slope <= 0:
                flow_direction = -2  # Sink
            
            flow_dir[i, j] = flow_direction
    
    return flow_dir


def calculate_flow_accumulation(flow_direction: np.ndarray) -> np.ndarray:
    """
    Calculate flow accumulation (number of upstream cells flowing into each cell).
    
    Higher values indicate stream channels and drainage paths.
    
    Args:
        flow_direction: D8 flow direction array
        
    Returns:
        Flow accumulation array
    """
    rows, cols = flow_direction.shape
    accumulation = np.ones_like(flow_direction, dtype=np.float32)
    
    # Direction to (drow, dcol) mapping
    dir_to_offset = {
        0: (0, 1),    # East
        1: (-1, 1),   # Northeast
        2: (-1, 0),   # North
        3: (-1, -1),  # Northwest
        4: (0, -1),   # West
        5: (1, -1),   # Southwest
        6: (1, 0),    # South
        7: (1, 1)     # Southeast
    }
    
    # Simple iterative approach (not most efficient but works)
    # In production, would use priority-flood or similar
    
    # Count how many cells flow into each cell
    for i in range(rows):
        for j in range(cols):
            direction = flow_direction[i, j]
            if direction >= 0 and direction <= 7:
                di, dj = dir_to_offset[direction]
                ni, nj = i + di, j + dj
                if 0 <= ni < rows and 0 <= nj < cols:
                    accumulation[ni, nj] += 1
    
    return accumulation


def generate_flood_spread(
    flood_mask: np.ndarray,
    dem: np.ndarray,
    max_distance_meters: float = 500.0,
    pixel_size: float = 10.0,
    nodata: float = -9999
) -> Dict[str, Any]:
    """
    Generate potential flood spread based on terrain.
    
    Simulates water spreading from detected flood areas following terrain.
    
    Methodology:
    1. Start from detected flood pixels
    2. Expand to neighboring pixels that are:
       - Lower elevation or within threshold
       - Within maximum distance
       - Hydraulically connected
    
    Args:
        flood_mask: Binary mask of detected flood
        dem: Digital Elevation Model
        max_distance_meters: Maximum spread distance
        pixel_size: Pixel size in meters
        nodata: No-data value
        
    Returns:
        Dictionary with spread_mask, probability_raster, flow_lines
    """
    logger.info("Generating flood spread visualization...")
    
    rows, cols = flood_mask.shape
    valid_mask = dem != nodata
    
    # Distance transform from flood areas
    # This gives distance to nearest flood pixel
    flood_distance = distance_transform_edt(flood_mask == 0) * pixel_size
    
    # Create spread mask based on distance and elevation
    spread_mask = np.zeros_like(flood_mask, dtype=bool)
    probability = np.zeros_like(flood_mask, dtype=np.float32)
    
    # Mark original flood areas
    spread_mask[flood_mask > 0] = True
    probability[flood_mask > 0] = 1.0
    
    # Expand to nearby low-lying areas
    max_pixels = int(max_distance_meters / pixel_size)
    
    # Get flood seed points
    flood_indices = np.where(flood_mask > 0)
    
    if len(flood_indices[0]) > 0:
        # Calculate mean flood elevation
        flood_elevations = dem[flood_mask > 0]
        if len(flood_elevations) > 0:
            mean_flood_elev = np.mean(flood_elevations)
            max_flood_elev = np.max(flood_elevations)
            
            # Potential flood area: lower than max flood elevation AND within distance
            elevation_condition = (dem <= max_flood_elev + 2.0) & valid_mask  # 2m buffer
            distance_condition = (flood_distance <= max_distance_meters)
            
            # Combine conditions
            potential_spread = elevation_condition & distance_condition
            
            # Calculate probability based on elevation difference and distance
            elev_diff = dem - mean_flood_elev
            elev_prob = np.clip(1 - (elev_diff / 5.0), 0, 1)  # 5m elevation decay
            dist_prob = np.clip(1 - (flood_distance / max_distance_meters), 0, 1)
            
            # Combined probability
            probability = np.zeros_like(dem, dtype=np.float32)
            probability[potential_spread] = (elev_prob[potential_spread] * 0.6 + 
                                             dist_prob[potential_spread] * 0.4)
            
            # Original flood has highest probability
            probability[flood_mask > 0] = 1.0
            
            spread_mask = potential_spread | (flood_mask > 0)
    
    # Generate flow arrows/lines
    flow_lines = extract_flow_lines(spread_mask, dem, pixel_size)
    
    stats = {
        "original_flood_pixels": int(np.sum(flood_mask > 0)),
        "spread_pixels": int(np.sum(spread_mask)),
        "spread_area_km2": float(np.sum(spread_mask) * pixel_size * pixel_size / 1e6),
        "max_spread_distance_m": float(max_distance_meters),
        "mean_probability": float(np.mean(probability[spread_mask])) if np.any(spread_mask) else 0.0
    }
    
    return {
        "spread_mask": spread_mask.astype(np.uint8),
        "probability": probability,
        "flow_lines": flow_lines,
        "stats": stats
    }


def extract_flow_lines(
    flood_mask: np.ndarray,
    dem: np.ndarray,
    pixel_size: float = 10.0,
    max_lines: int = 50
) -> List[Dict[str, Any]]:
    """
    Extract representative flow lines from flood area.
    
    Creates arrow/line features showing potential flow direction.
    
    Args:
        flood_mask: Binary flood/spread mask
        dem: Digital Elevation Model
        pixel_size: Pixel size in meters
        max_lines: Maximum number of flow lines to generate
        
    Returns:
        List of GeoJSON-like line features
    """
    from skimage.measure import find_contours
    
    lines = []
    
    # Find contours of flood area
    contours = find_contours(flood_mask.astype(float), 0.5)
    
    # Sample points along contours and trace flow paths
    for contour in contours:
        # Sample every nth point to avoid too many lines
        step = max(1, len(contour) // min(max_lines, len(contour)))
        
        for idx in range(0, len(contour), step):
            if len(lines) >= max_lines:
                break
            
            row, col = contour[idx]
            row, col = int(row), int(col)
            
            # Trace flow path downhill
            path_coords = []
            curr_row, curr_col = row, col
            max_steps = 20
            
            for _ in range(max_steps):
                if not (0 <= curr_row < dem.shape[0] and 0 <= curr_col < dem.shape[1]):
                    break
                
                # Convert to geographic coordinates (simplified)
                x = curr_col * pixel_size
                y = curr_row * pixel_size
                path_coords.append([x, y])
                
                # Find steepest downslope neighbor
                min_elev = dem[curr_row, curr_col]
                next_pos = None
                
                for di in [-1, 0, 1]:
                    for dj in [-1, 0, 1]:
                        if di == 0 and dj == 0:
                            continue
                        ni, nj = curr_row + di, curr_col + dj
                        if 0 <= ni < dem.shape[0] and 0 <= nj < dem.shape[1]:
                            if dem[ni, nj] < min_elev:
                                min_elev = dem[ni, nj]
                                next_pos = (ni, nj)
                
                if next_pos is None:
                    break  # Reached local minimum
                
                curr_row, curr_col = next_pos
            
            if len(path_coords) >= 2:
                lines.append({
                    "type": "Feature",
                    "properties": {"flow_direction": "downslope"},
                    "geometry": {
                        "type": "LineString",
                        "coordinates": path_coords
                    }
                })
    
    return lines


def create_flood_arrows(
    flow_direction: np.ndarray,
    flood_mask: np.ndarray,
    pixel_size: float = 10.0
) -> List[Dict[str, Any]]:
    """
    Create arrow markers showing flow direction in flood areas.
    
    Args:
        flow_direction: D8 flow direction array
        flood_mask: Flood extent mask
        pixel_size: Pixel size in meters
        
    Returns:
        List of arrow features for map visualization
    """
    arrows = []
    
    # Sample points in flood area
    indices = np.where(flood_mask > 0)
    
    # Sample every 5th pixel to avoid clutter
    step = 5
    for i in range(0, len(indices[0]), step):
        row = indices[0][i]
        col = indices[1][i]
        
        direction = flow_direction[row, col]
        if direction < 0 or direction > 7:
            continue
        
        # Direction to angle mapping (degrees from North, clockwise)
        dir_to_angle = {
            0: 90,    # East
            1: 45,    # Northeast
            2: 0,     # North
            3: 315,   # Northwest
            4: 270,   # West
            5: 225,   # Southwest
            6: 180,   # South
            7: 135    # Southeast
        }
        
        x = col * pixel_size
        y = row * pixel_size
        
        arrows.append({
            "type": "Feature",
            "properties": {
                "angle": dir_to_angle[direction],
                "symbol": "arrow"
            },
            "geometry": {
                "type": "Point",
                "coordinates": [x, y]
            }
        })
    
    return arrows


def generate_inundation_depth(
    flood_mask: np.ndarray,
    dem: np.ndarray,
    water_level: Optional[float] = None,
    nodata: float = -9999
) -> np.ndarray:
    """
    Estimate inundation depth based on DEM and flood extent.
    
    Simplified method: assumes flat water surface at median flood elevation.
    
    Args:
        flood_mask: Binary flood mask
        dem: Digital Elevation Model
        water_level: Fixed water level (if known), else calculated from flood pixels
        nodata: No-data value
        
    Returns:
        Water depth array (meters)
    """
    valid_mask = dem != nodata
    
    if water_level is None:
        # Estimate water level from flood pixels
        flood_elevations = dem[(flood_mask > 0) & valid_mask]
        if len(flood_elevations) > 0:
            water_level = np.percentile(flood_elevations, 90)  # Use 90th percentile
        else:
            return np.zeros_like(dem)
    
    # Depth = water_level - ground_elevation
    depth = water_level - dem
    
    # Only positive depths in flood area
    depth = np.maximum(depth, 0)
    depth[~(flood_mask > 0)] = 0
    depth[~valid_mask] = nodata
    
    return depth
