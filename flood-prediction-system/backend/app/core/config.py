"""Application configuration using Pydantic Settings"""
from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Application
    APP_ENV: str = "development"
    DEBUG: bool = True
    SECRET_KEY: str = "dev-secret-key-change-in-production"
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "/app/logs/app.log"
    
    # CORS
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173"
    
    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]
    
    # Database
    POSTGRES_USER: str = "flood_user"
    POSTGRES_PASSWORD: str = "change_this_password"
    POSTGRES_DB: str = "flood_prediction"
    POSTGRES_HOST: str = "postgres"
    POSTGRES_PORT: int = 5432
    
    @property
    def database_url(self) -> str:
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
    
    @property
    def async_database_url(self) -> str:
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
    
    # Redis/Celery
    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    
    @property
    def celery_broker_url(self) -> str:
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
    
    # Data directories
    DATA_DIR: str = "/app/data"
    MAX_AOI_SIZE_KM2: float = 100.0
    MAX_DOWNLOAD_SIZE_MB: int = 500
    
    # Processing parameters
    DEFAULT_BACKSCATTER_THRESHOLD: float = -20.0
    DEFAULT_NDWI_THRESHOLD: float = 0.3
    DEFAULT_MNDWI_THRESHOLD: float = 0.0
    MIN_CONNECTED_COMPONENT_SIZE: int = 100
    
    # External API credentials (optional)
    COPEERNICUS_USERNAME: str = ""
    COPEERNICUS_PASSWORD: str = ""
    SENTINEL_HUB_CLIENT_ID: str = ""
    SENTINEL_HUB_CLIENT_SECRET: str = ""
    NASA_EARTHDATA_USERNAME: str = ""
    NASA_EARTHDATA_PASSWORD: str = ""
    OPENWEATHERMAP_API_KEY: str = ""
    MAPBOX_ACCESS_TOKEN: str = ""
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
