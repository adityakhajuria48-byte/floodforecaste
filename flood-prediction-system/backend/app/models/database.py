"""
Database Models for Flood Prediction System
Uses SQLAlchemy with GeoAlchemy2 for PostGIS support
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, JSON, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import TIMESTAMP
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.sql import func
import enum
from geoalchemy2 import Geometry

Base = declarative_base()


class JobStatus(str, enum.Enum):
    QUEUED = "queued"
    DOWNLOADING = "downloading"
    PROCESSING = "processing"
    ANALYZING = "analyzing"
    PREDICTING = "predicting"
    COMPLETED = "completed"
    FAILED = "failed"


class AnalysisType(str, enum.Enum):
    FLOOD_DETECTION = "flood_detection"
    HISTORICAL_ANALYSIS = "historical_analysis"
    RISK_PREDICTION = "risk_prediction"
    FLOW_ANALYSIS = "flow_analysis"


class SatelliteSource(str, enum.Enum):
    SENTINEL1 = "sentinel1"
    SENTINEL2 = "sentinel2"


class User(Base):
    """User table for authentication (optional)"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    
    # Relationships
    aois = relationship("AOI", back_populates="user", cascade="all, delete-orphan")
    analysis_jobs = relationship("AnalysisJob", back_populates="user", cascade="all, delete-orphan")


class AOI(Base):
    """Area of Interest defined by user"""
    __tablename__ = "aois"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    # Geometry stored as GeoJSON
    geometry = Column(Geometry('POLYGON', srid=4326), nullable=False)
    centroid_lat = Column(Float, nullable=False)
    centroid_lon = Column(Float, nullable=False)
    area_km2 = Column(Float, nullable=False)
    
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="aois")
    satellite_scenes = relationship("SatelliteScene", back_populates="aoi", cascade="all, delete-orphan")
    analysis_jobs = relationship("AnalysisJob", back_populates="aoi", cascade="all, delete-orphan")


class SatelliteScene(Base):
    """Metadata for downloaded satellite scenes"""
    __tablename__ = "satellite_scenes"
    
    id = Column(Integer, primary_key=True, index=True)
    aoi_id = Column(Integer, ForeignKey("aois.id"), nullable=False)
    
    # Scene identification
    scene_id = Column(String(255), unique=True, nullable=False, index=True)
    source = Column(Enum(SatelliteSource), nullable=False)
    product_type = Column(String(100), nullable=True)  # GRD, L1C, etc.
    
    # Acquisition info
    acquisition_date = Column(DateTime(timezone=True), nullable=False, index=True)
    sensing_start = Column(DateTime(timezone=True), nullable=True)
    sensing_stop = Column(DateTime(timezone=True), nullable=True)
    
    # Processing info
    processing_level = Column(String(50), nullable=True)
    orbit_number = Column(Integer, nullable=True)
    orbit_direction = Column(String(20), nullable=True)  # ASCENDING/DESCENDING
    
    # Quality metrics
    cloud_coverage = Column(Float, nullable=True)  # For Sentinel-2
    polarization = Column(String(50), nullable=True)  # For Sentinel-1 (VV, VH)
    
    # File locations
    file_path = Column(String(512), nullable=True)
    file_size_mb = Column(Float, nullable=True)
    download_status = Column(String(50), default="pending")
    
    # Bounding box
    bbox_min_lat = Column(Float, nullable=False)
    bbox_max_lat = Column(Float, nullable=False)
    bbox_min_lon = Column(Float, nullable=False)
    bbox_max_lon = Column(Float, nullable=False)
    
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    
    # Relationships
    aoi = relationship("AOI", back_populates="satellite_scenes")


class AnalysisJob(Base):
    """Tracking for analysis jobs (async processing)"""
    __tablename__ = "analysis_jobs"
    
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(String(100), unique=True, nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    aoi_id = Column(Integer, ForeignKey("aois.id"), nullable=False)
    
    # Job type
    analysis_type = Column(Enum(AnalysisType), nullable=False)
    
    # Parameters
    parameters = Column(JSON, nullable=True)
    
    # Status tracking
    status = Column(Enum(JobStatus), default=JobStatus.QUEUED, index=True)
    progress = Column(Integer, default=0)  # 0-100
    message = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)
    
    # Timing
    queued_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    started_at = Column(TIMESTAMP(timezone=True), nullable=True)
    completed_at = Column(TIMESTAMP(timezone=True), nullable=True)
    
    # Results location
    result_file_path = Column(String(512), nullable=True)
    result_geojson_path = Column(String(512), nullable=True)
    result_geotiff_path = Column(String(512), nullable=True)
    
    # Statistics (stored as JSON for flexibility)
    statistics = Column(JSON, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="analysis_jobs")
    aoi = relationship("AOI", back_populates="analysis_jobs")


class FloodEvent(Base):
    """Detected flood events from analysis"""
    __tablename__ = "flood_events"
    
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("analysis_jobs.id"), nullable=False)
    
    # Event info
    event_date = Column(DateTime(timezone=True), nullable=False, index=True)
    detection_method = Column(String(100), nullable=False)  # SAR, NDWI, MNDWI
    
    # Statistics
    flooded_area_km2 = Column(Float, nullable=False)
    affected_percentage = Column(Float, nullable=True)
    
    # Water classification
    permanent_water_km2 = Column(Float, nullable=True)
    temporary_flood_km2 = Column(Float, nullable=True)
    uncertain_area_km2 = Column(Float, nullable=True)
    
    # Confidence
    confidence_score = Column(Float, nullable=True)  # 0-1
    
    # Geometry
    flood_geometry = Column(Geometry('MULTIPOLYGON', srid=4326), nullable=True)
    
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())


class RiskPrediction(Base):
    """Flood risk prediction results"""
    __tablename__ = "risk_predictions"
    
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("analysis_jobs.id"), nullable=False)
    
    # Prediction info
    prediction_date = Column(TIMESTAMP(timezone=True), server_default=func.now())
    model_version = Column(String(50), nullable=False)
    
    # Risk statistics
    low_risk_area_km2 = Column(Float, nullable=True)
    moderate_risk_area_km2 = Column(Float, nullable=True)
    high_risk_area_km2 = Column(Float, nullable=True)
    very_high_risk_area_km2 = Column(Float, nullable=True)
    
    # Model performance
    model_confidence = Column(Float, nullable=True)
    feature_importance = Column(JSON, nullable=True)
    
    # Raster output
    risk_raster_path = Column(String(512), nullable=True)
    probability_raster_path = Column(String(512), nullable=True)
    
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())


class HistoricalFloodStat(Base):
    """Historical flood statistics"""
    __tablename__ = "historical_flood_stats"
    
    id = Column(Integer, primary_key=True, index=True)
    aoi_id = Column(Integer, ForeignKey("aois.id"), nullable=False)
    
    # Time period
    year = Column(Integer, nullable=False, index=True)
    month = Column(Integer, nullable=True)
    
    # Statistics
    max_flooded_area_km2 = Column(Float, nullable=False)
    avg_flooded_area_km2 = Column(Float, nullable=True)
    flood_frequency = Column(Integer, nullable=True)  # Number of events
    flood_duration_days = Column(Float, nullable=True)
    
    # Seasonal info
    is_peak_season = Column(Boolean, default=False)
    
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
