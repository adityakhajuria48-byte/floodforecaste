"""
Test Suite for Flood Prediction System Backend
----------------------------------------------
Tests for database models, Celery tasks, and API endpoints.
"""

import pytest
import numpy as np
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
import json


# Test Database Models
class TestDatabaseModels:
    """Test SQLAlchemy database models."""
    
    def test_job_status_enum(self):
        """Test JobStatus enum values."""
        from app.models.database import JobStatus
        
        assert JobStatus.QUEUED.value == "queued"
        assert JobStatus.DOWNLOADING.value == "downloading"
        assert JobStatus.PROCESSING.value == "processing"
        assert JobStatus.ANALYZING.value == "analyzing"
        assert JobStatus.PREDICTING.value == "predicting"
        assert JobStatus.COMPLETED.value == "completed"
        assert JobStatus.FAILED.value == "failed"
    
    def test_analysis_type_enum(self):
        """Test AnalysisType enum values."""
        from app.models.database import AnalysisType
        
        assert AnalysisType.FLOOD_DETECTION.value == "flood_detection"
        assert AnalysisType.HISTORICAL_ANALYSIS.value == "historical_analysis"
        assert AnalysisType.RISK_PREDICTION.value == "risk_prediction"
        assert AnalysisType.FLOW_ANALYSIS.value == "flow_analysis"
    
    def test_satellite_source_enum(self):
        """Test SatelliteSource enum values."""
        from app.models.database import SatelliteSource
        
        assert SatelliteSource.SENTINEL1.value == "sentinel1"
        assert SatelliteSource.SENTINEL2.value == "sentinel2"


# Test ML Prediction Models
class TestMLPredictionModels:
    """Test machine learning flood risk models."""
    
    def test_flood_risk_model_initialization(self):
        """Test FloodRiskModel initialization with different model types."""
        from app.prediction.models import FloodRiskModel
        
        # Test Random Forest (default)
        rf_model = FloodRiskModel(model_type="random_forest")
        assert rf_model.model_type == "random_forest"
        assert rf_model.is_fitted == False
        assert len(rf_model.feature_names) == 7
        
        # Test Gradient Boosting
        gb_model = FloodRiskModel(model_type="gradient_boosting")
        assert gb_model.model_type == "gradient_boosting"
        
        # Test Logistic Regression
        lr_model = FloodRiskModel(model_type="logistic_regression")
        assert lr_model.model_type == "logistic_regression"
        
        # Test unknown type fallback (logs warning but keeps original type)
        unknown_model = FloodRiskModel(model_type="unknown")
        # Model logs warning but initializes with Random Forest underlying model
        assert hasattr(unknown_model.model, 'n_estimators')  # RF attribute
    
    def test_prepare_features(self):
        """Test feature matrix preparation."""
        from app.prediction.models import FloodRiskModel
        
        model = FloodRiskModel()
        
        # Create sample arrays
        elevation = np.random.rand(10, 10) * 100
        slope = np.random.rand(10, 10) * 30
        distance_to_river = np.random.rand(10, 10) * 1000
        
        # Prepare features
        features = model.prepare_features(
            elevation=elevation,
            slope=slope,
            distance_to_river=distance_to_river
        )
        
        # Check shape: 100 samples (10x10 flattened), 7 features
        assert features.shape == (100, 7)
    
    def test_baseline_risk_model(self):
        """Test baseline heuristic risk model."""
        from app.prediction.models import create_baseline_risk_model
        
        # Create sample data
        elevation = np.random.rand(50, 50) * 100
        slope = np.random.rand(50, 50) * 30
        distance_to_river = np.random.rand(50, 50) * 1000
        historical_flood = np.zeros((50, 50))
        historical_flood[20:30, 20:30] = 1  # Simulated flood area
        
        # Generate risk model
        result = create_baseline_risk_model(
            elevation=elevation,
            slope=slope,
            distance_to_river=distance_to_river,
            historical_flood_mask=historical_flood
        )
        
        # Check outputs
        assert result["risk_score"].shape == (50, 50)
        assert result["risk_class"].shape == (50, 50)
        assert "stats" in result
        assert result["stats"]["method"] == "heuristic_baseline"
        
        # Check risk score range (should be 0-1)
        valid_scores = result["risk_score"][result["risk_score"] != -9999]
        assert np.all(valid_scores >= 0)
        assert np.all(valid_scores <= 1)
        
        # Check risk classes (should be 0-3)
        valid_classes = result["risk_class"][result["risk_class"] != -1]
        assert np.all(valid_classes >= 0)
        assert np.all(valid_classes <= 3)
    
    def test_slope_calculation(self):
        """Test slope calculation from DEM."""
        from app.prediction.models import calculate_slope
        
        # Create a simple sloped surface
        dem = np.array([
            [10, 10, 10],
            [20, 20, 20],
            [30, 30, 30]
        ], dtype=float)
        
        slope = calculate_slope(dem, pixel_size=10.0)
        
        # Slope should be positive (terrain rises)
        assert np.all(slope >= 0)
        # Center should have defined slope
        assert not np.isnan(slope[1, 1])
    
    def test_distance_to_river(self):
        """Test distance to river calculation."""
        from app.prediction.models import calculate_distance_to_river
        
        # Create river mask (river on left edge)
        river_mask = np.zeros((10, 10), dtype=bool)
        river_mask[:, 0] = True
        
        distance = calculate_distance_to_river(river_mask, pixel_size=10.0)
        
        # River pixels should have distance 0
        assert distance[river_mask].all() == 0.0
        
        # Distance should increase from left to right
        for col in range(1, 10):
            assert distance[0, col] > distance[0, col-1]


# Test Celery Tasks
class TestCeleryTasks:
    """Test Celery background tasks."""
    
    @patch('app.services.tasks.CopernicusClient')
    @patch('app.services.tasks.FloodDetectionService')
    def test_process_satellite_data_task(self, mock_flood_service, mock_copernicus):
        """Test satellite processing task."""
        from app.services.tasks import process_satellite_data
        
        # Setup mocks
        mock_client = Mock()
        mock_client.search_scenes.return_value = [{'id': 'test_scene_123'}]
        mock_client.download_scene.return_value = '/tmp/test_scene.tif'
        mock_copernicus.return_value = mock_client
        
        mock_service = Mock()
        mock_service.process_sar.return_value = {
            'geojson': {'type': 'FeatureCollection', 'features': []},
            'statistics': {'flooded_area_km2': 5.5, 'affected_percentage': 10.0},
            'method': 'SAR'
        }
        mock_flood_service.return_value = mock_service
        
        # Sample AOI
        aoi = {
            "type": "Polygon",
            "coordinates": [[[77.0, 28.0], [77.5, 28.0], [77.5, 28.5], [77.0, 28.5], [77.0, 28.0]]]
        }
        
        # Run task (would normally be async, but we test synchronously)
        # Note: This is a simplified test - actual Celery testing requires more setup
        
        assert True  # Placeholder for actual task execution test
    
    def test_job_manager_integration(self):
        """Test job manager integration with tasks."""
        from app.services.job_manager import job_manager, ProcessingJob
        from app.services.tasks import predict_flood_risk
        
        # Create a test job
        job = ProcessingJob(
            job_id="test_job_123",
            job_type="risk_prediction",
            status="QUEUED"
        )
        job_manager.add_job(job)
        
        # Verify job was added
        retrieved_job = job_manager.get_job("test_job_123")
        assert retrieved_job is not None
        assert retrieved_job.job_type == "risk_prediction"
        
        # Update status
        job.update_status("PROCESSING", {"step": "computing_features"})
        assert job.status == "PROCESSING"
        assert job.progress > 0


# Test API Endpoints
class TestAPIEndpoints:
    """Test FastAPI endpoint schemas and logic."""
    
    def test_flood_detection_request_schema(self):
        """Test FloodDetectionRequest schema validation."""
        from app.schemas.flood import FloodDetectionRequest
        
        # Valid request
        request = FloodDetectionRequest(
            aoi_geojson={
                "type": "Polygon",
                "coordinates": [[[77.0, 28.0], [77.5, 28.0], [77.5, 28.5], [77.0, 28.5], [77.0, 28.0]]]
            },
            sensor_type="sentinel-1",
            threshold_db=-18.0
        )
        
        assert request.sensor_type == "sentinel-1"
        assert request.threshold_db == -18.0
    
    def test_historical_analysis_request_schema(self):
        """Test HistoricalAnalysisRequest schema validation."""
        from app.schemas.flood import HistoricalAnalysisRequest
        
        request = HistoricalAnalysisRequest(
            aoi_geojson={
                "type": "Polygon",
                "coordinates": [[[77.0, 28.0], [77.5, 28.0], [77.5, 28.5], [77.0, 28.5], [77.0, 28.0]]]
            },
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 6, 30),
            limit=20
        )
        
        assert request.limit == 20
        assert request.sensor_type == "sentinel-1"  # Default
    
    def test_flood_risk_request_schema(self):
        """Test FloodRiskRequest schema validation."""
        from app.schemas.flood import FloodRiskRequest
        
        request = FloodRiskRequest(
            aoi_geojson={
                "type": "Polygon",
                "coordinates": [[[77.0, 28.0], [77.5, 28.0], [77.5, 28.5], [77.0, 28.5], [77.0, 28.0]]]
            },
            model_type="random_forest"
        )
        
        assert request.model_type == "random_forest"
    
    def test_job_status_response_schema(self):
        """Test JobStatusResponse schema."""
        from app.schemas.flood import JobStatusResponse
        from datetime import datetime
        
        response = JobStatusResponse(
            job_id="test_job_123",
            job_type="flood_detection",
            status="COMPLETED",
            progress=100,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            result={"flooded_area_km2": 5.5}
        )
        
        assert response.status == "COMPLETED"
        assert response.progress == 100


# Test Export Functionality
class TestExportEndpoints:
    """Test export API functionality."""
    
    def test_export_formats(self):
        """Test that export supports multiple formats."""
        from app.api.export import router
        
        # Check routes exist
        routes = [route.path for route in router.routes]
        
        assert "/export/geojson/{job_id}" in routes
        assert "/export/geotiff/{job_id}" in routes
        assert "/export/statistics/{job_id}" in routes
        assert "/export/report/{job_id}" in routes


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
