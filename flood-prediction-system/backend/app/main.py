"""
Flood Prediction System - FastAPI Backend
Main application entry point
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger
import sys

from app.core.config import settings
from app.api import location, satellite, flood, export, status

# Configure logging
logger.remove()
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
    level=settings.LOG_LEVEL,
)
logger.add(
    settings.LOG_FILE,
    rotation="500 MB",
    retention="10 days",
    level=settings.LOG_LEVEL,
)

app = FastAPI(
    title="Flood Prediction System API",
    description="""
## AI-Powered Flood Prediction & Satellite Analysis System

This API provides endpoints for:
- **Location Search**: Geocoding and reverse geocoding
- **Satellite Data**: Search and download Sentinel-1/2 imagery
- **Flood Detection**: SAR-based flood extent mapping
- **Historical Analysis**: Temporal flood pattern analysis
- **Risk Prediction**: ML-based flood susceptibility modeling
- **Export**: Download results in various formats

### Authentication
Most endpoints require API credentials configured via environment variables.

### Rate Limiting
Expensive operations (satellite download, processing) are queued and processed asynchronously.
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exception handlers
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "type": type(exc).__name__},
    )

# Include routers
app.include_router(location.router, prefix="/api/location", tags=["Location"])
app.include_router(satellite.router, prefix="/api/satellite", tags=["Satellite"])
app.include_router(flood.router, prefix="/api/flood", tags=["Flood Analysis"])
app.include_router(export.router, prefix="/api/export", tags=["Export"])
app.include_router(status.router, prefix="/api/status", tags=["Status"])

# Health check
@app.get("/health", tags=["Health"])
async def health_check():
    return {
        "status": "healthy",
        "version": "1.0.0",
        "environment": settings.APP_ENV,
    }

@app.get("/", tags=["Root"])
async def root():
    return {
        "message": "Flood Prediction System API",
        "docs": "/docs",
        "health": "/health",
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
    )
