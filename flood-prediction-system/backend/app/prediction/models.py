"""
Flood Risk Prediction Models
----------------------------
Machine learning models for estimating flood susceptibility and risk.
"""

import numpy as np
from typing import Dict, Any, Optional, Tuple, List
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
import logging
import joblib
from pathlib import Path

logger = logging.getLogger(__name__)


class FloodRiskModel:
    """
    Flood Risk Prediction Model.
    
    Uses environmental and historical factors to estimate flood susceptibility.
    
    Features used:
    - Elevation (DEM)
    - Slope
    - Distance to river
    - Historical flood frequency
    - Land cover type
    - NDWI/MNDWI water index
    - Rainfall intensity (if available)
    - Soil type (if available)
    
    Output:
    - Risk probability (0-1)
    - Risk class (Low, Moderate, High, Very High)
    """
    
    def __init__(self, model_type: str = "random_forest"):
        self.model_type = model_type
        self.model = self._initialize_model()
        self.scaler = StandardScaler()
        self.is_fitted = False
        self.feature_names = [
            "elevation",
            "slope",
            "distance_to_river",
            "historical_flood_freq",
            "land_cover",
            "water_index",
            "rainfall_intensity"
        ]
    
    def _initialize_model(self):
        """Initialize the ML model based on type."""
        if self.model_type == "random_forest":
            return RandomForestClassifier(
                n_estimators=100,
                max_depth=10,
                min_samples_split=5,
                min_samples_leaf=2,
                class_weight='balanced',
                random_state=42,
                n_jobs=-1
            )
        elif self.model_type == "gradient_boosting":
            return GradientBoostingClassifier(
                n_estimators=100,
                max_depth=5,
                learning_rate=0.1,
                random_state=42
            )
        elif self.model_type == "logistic_regression":
            return LogisticRegression(
                class_weight='balanced',
                max_iter=1000,
                random_state=42
            )
        else:
            logger.warning(f"Unknown model type {self.model_type}, using Random Forest")
            return RandomForestClassifier(n_estimators=100, random_state=42)
    
    def prepare_features(
        self,
        elevation: np.ndarray,
        slope: np.ndarray,
        distance_to_river: np.ndarray,
        historical_flood_freq: Optional[np.ndarray] = None,
        land_cover: Optional[np.ndarray] = None,
        water_index: Optional[np.ndarray] = None,
        rainfall_intensity: Optional[np.ndarray] = None
    ) -> np.ndarray:
        """
        Prepare feature matrix from input rasters.
        
        All inputs should be 2D numpy arrays with same shape.
        """
        # Flatten arrays
        elev_flat = elevation.flatten()
        slope_flat = slope.flatten()
        dist_flat = distance_to_river.flatten()
        
        # Handle optional features with defaults
        if historical_flood_freq is None:
            hist_flat = np.zeros_like(elev_flat)
        else:
            hist_flat = historical_flood_freq.flatten()
        
        if land_cover is None:
            lc_flat = np.zeros_like(elev_flat)
        else:
            lc_flat = land_cover.flatten()
        
        if water_index is None:
            wi_flat = np.zeros_like(elev_flat)
        else:
            wi_flat = water_index.flatten()
        
        if rainfall_intensity is None:
            rain_flat = np.zeros_like(elev_flat)
        else:
            rain_flat = rainfall_intensity.flatten()
        
        # Stack features
        feature_matrix = np.column_stack([
            elev_flat,
            slope_flat,
            dist_flat,
            hist_flat,
            lc_flat,
            wi_flat,
            rain_flat
        ])
        
        return feature_matrix
    
    def fit(
        self,
        X: np.ndarray,
        y: np.ndarray,
        sample_weight: Optional[np.ndarray] = None
    ):
        """
        Train the model.
        
        Args:
            X: Feature matrix (n_samples, n_features)
            y: Labels (0=no flood, 1=flood)
            sample_weight: Optional sample weights
        """
        logger.info(f"Fitting {self.model_type} model with {X.shape[0]} samples...")
        
        # Scale features
        X_scaled = self.scaler.fit_transform(X)
        
        # Train model
        if sample_weight is not None:
            self.model.fit(X_scaled, y, sample_weight=sample_weight)
        else:
            self.model.fit(X_scaled, y)
        
        self.is_fitted = True
        logger.info("Model training complete.")
    
    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """
        Predict flood risk probability.
        
        Args:
            X: Feature matrix
            
        Returns:
            Probability of flood (0-1)
        """
        if not self.is_fitted:
            raise ValueError("Model must be fitted before prediction")
        
        X_scaled = self.scaler.transform(X)
        proba = self.model.predict_proba(X_scaled)[:, 1]  # Probability of class 1 (flood)
        
        return proba
    
    def predict(self, X: np.ndarray, threshold: float = 0.5) -> np.ndarray:
        """
        Predict flood/no-flood classification.
        
        Args:
            X: Feature matrix
            threshold: Probability threshold for classification
            
        Returns:
            Binary predictions (0 or 1)
        """
        proba = self.predict_proba(X)
        return (proba >= threshold).astype(int)
    
    def predict_risk_class(self, proba: np.ndarray) -> np.ndarray:
        """
        Convert probability to risk class.
        
        Classes:
        0: Low Risk (0-0.25)
        1: Moderate Risk (0.25-0.5)
        2: High Risk (0.5-0.75)
        3: Very High Risk (0.75-1.0)
        """
        risk_class = np.zeros_like(proba, dtype=int)
        risk_class[(proba >= 0.25) & (proba < 0.5)] = 1
        risk_class[(proba >= 0.5) & (proba < 0.75)] = 2
        risk_class[proba >= 0.75] = 3
        
        return risk_class
    
    def get_feature_importance(self) -> Dict[str, float]:
        """Get feature importance scores."""
        if not self.is_fitted:
            return {}
        
        if hasattr(self.model, 'feature_importances_'):
            importance = self.model.feature_importances_
            return dict(zip(self.feature_names, importance.tolist()))
        else:
            # For logistic regression, use coefficient magnitude
            coeffs = np.abs(self.model.coef_[0])
            return dict(zip(self.feature_names, coeffs.tolist()))
    
    def save(self, path: str):
        """Save model to disk."""
        joblib.dump({
            'model': self.model,
            'scaler': self.scaler,
            'model_type': self.model_type,
            'is_fitted': self.is_fitted
        }, path)
        logger.info(f"Model saved to {path}")
    
    @classmethod
    def load(cls, path: str) -> 'FloodRiskModel':
        """Load model from disk."""
        data = joblib.load(path)
        instance = cls(model_type=data['model_type'])
        instance.model = data['model']
        instance.scaler = data['scaler']
        instance.is_fitted = data['is_fitted']
        return instance


def create_baseline_risk_model(
    elevation: np.ndarray,
    slope: np.ndarray,
    distance_to_river: np.ndarray,
    historical_flood_mask: Optional[np.ndarray] = None,
    nodata: float = -9999
) -> Dict[str, Any]:
    """
    Create a baseline flood risk map using heuristic rules.
    
    This is used when no training data is available.
    
    Rules:
    - Lower elevation = higher risk
    - Lower slope = higher risk (water accumulates)
    - Closer to river = higher risk
    - Historical flooding = much higher risk
    """
    logger.info("Creating baseline risk model using heuristic rules...")
    
    # Normalize inputs (0-1 scale, higher = more risky)
    
    # Elevation risk: lower is riskier
    elev_valid = elevation[elevation != nodata]
    if len(elev_valid) > 0:
        elev_norm = 1 - (elevation - elev_valid.min()) / (elev_valid.max() - elev_valid.min() + 1e-6)
    else:
        elev_norm = np.zeros_like(elevation)
    elev_norm[elevation == nodata] = nodata
    
    # Slope risk: flatter is riskier
    slope_valid = slope[slope != nodata]
    if len(slope_valid) > 0:
        slope_max = slope_valid.max()
        if slope_max > 0:
            slope_norm = 1 - (slope / slope_max)
        else:
            slope_norm = np.ones_like(slope)
    else:
        slope_norm = np.zeros_like(slope)
    slope_norm[slope == nodata] = nodata
    
    # Distance to river risk: closer is riskier
    dist_valid = distance_to_river[distance_to_river != nodata]
    if len(dist_valid) > 0:
        dist_max = dist_valid.max()
        if dist_max > 0:
            dist_norm = 1 - (distance_to_river / dist_max)
        else:
            dist_norm = np.ones_like(distance_to_river)
    else:
        dist_norm = np.zeros_like(distance_to_river)
    dist_norm[distance_to_river == nodata] = nodata
    
    # Historical flood risk
    if historical_flood_mask is not None:
        hist_norm = historical_flood_mask.astype(float)
    else:
        hist_norm = np.zeros_like(elevation)
    
    # Combine risks (weighted average)
    weights = {
        'elevation': 0.25,
        'slope': 0.20,
        'distance': 0.30,
        'historical': 0.25
    }
    
    risk_score = (
        weights['elevation'] * elev_norm +
        weights['slope'] * slope_norm +
        weights['distance'] * dist_norm +
        weights['historical'] * hist_norm
    )
    
    # Clip to 0-1 range
    risk_score = np.clip(risk_score, 0, 1)
    risk_score[elevation == nodata] = -9999  # Reset nodata
    
    # Classify risk
    risk_class = np.zeros_like(risk_score, dtype=int)
    risk_class[(risk_score >= 0.25) & (risk_score < 0.5)] = 1
    risk_class[(risk_score >= 0.5) & (risk_score < 0.75)] = 2
    risk_class[risk_score >= 0.75] = 3
    risk_class[elevation == nodata] = -1  # Mark nodata in class too
    
    stats = {
        "mean_risk_score": float(np.mean(risk_score[risk_score != nodata])),
        "std_risk_score": float(np.std(risk_score[risk_score != nodata])),
        "low_risk_pixels": int(np.sum(risk_class == 0)),
        "moderate_risk_pixels": int(np.sum(risk_class == 1)),
        "high_risk_pixels": int(np.sum(risk_class == 2)),
        "very_high_risk_pixels": int(np.sum(risk_class == 3)),
        "method": "heuristic_baseline"
    }
    
    return {
        "risk_score": risk_score,
        "risk_class": risk_class,
        "stats": stats,
        "components": {
            "elevation_risk": elev_norm,
            "slope_risk": slope_norm,
            "distance_risk": dist_norm,
            "historical_risk": hist_norm
        }
    }


def calculate_slope(dem: np.ndarray, pixel_size: float = 10.0) -> np.ndarray:
    """
    Calculate slope from DEM using finite differences.
    
    Args:
        dem: 2D elevation array
        pixel_size: Pixel size in meters
        
    Returns:
        Slope in degrees
    """
    # Calculate gradients
    grad_y, grad_x = np.gradient(dem, pixel_size)
    
    # Slope in radians
    slope_rad = np.arctan(np.sqrt(grad_x**2 + grad_y**2))
    
    # Convert to degrees
    slope_deg = np.degrees(slope_rad)
    
    return slope_deg


def calculate_distance_to_river(
    river_mask: np.ndarray,
    pixel_size: float = 10.0
) -> np.ndarray:
    """
    Calculate Euclidean distance to nearest river pixel.
    
    Args:
        river_mask: Binary mask of river locations
        pixel_size: Pixel size in meters
        
    Returns:
        Distance array in meters
    """
    from scipy.ndimage import distance_transform_edt
    
    # Distance transform (distance to nearest True pixel)
    distance_pixels = distance_transform_edt(~river_mask)
    
    # Convert to meters
    distance_meters = distance_pixels * pixel_size
    
    return distance_meters
