# Flood Prediction System - Architecture Document

## 1. System Overview

This is a web-based flood prediction and satellite analysis system that:
- Retrieves Sentinel-1 SAR and Sentinel-2 optical satellite imagery
- Detects flood extent using backscatter analysis and water indices
- Analyzes historical flood patterns
- Predicts flood risk using ML models
- Visualizes results on an interactive GIS map

## 2. Technology Stack

### Frontend
- **React 18** - Modern UI framework with hooks and concurrent rendering
- **TypeScript** - Type safety and better developer experience
- **Vite** - Fast build tool and dev server
- **MapLibre GL JS** - Open-source WebGL map library (Leaflet alternative)
- **Tailwind CSS** - Utility-first CSS framework
- **Recharts** - Charting library for time-series visualization
- **Axios** - HTTP client for API communication
- **Zustand** - Lightweight state management

### Backend
- **Python 3.10+** - Primary backend language
- **FastAPI** - Modern async web framework with automatic OpenAPI docs
- **SQLAlchemy** - ORM for database operations
- **Pydantic** - Data validation and settings management
- **Celery** - Distributed task queue for background processing
- **Redis** - Message broker for Celery and caching

### Geospatial & Remote Sensing
- **GDAL/OGR** - Core geospatial data translation library
- **Rasterio** - Read/write geospatial raster data
- **GeoPandas** - Geospatial data manipulation
- **Shapely** - Geometric objects and operations
- **PyProj** - Cartographic projections and coordinate transformations
- **xarray + rioxarray** - Multi-dimensional array handling with geospatial metadata
- **NumPy + SciPy** - Numerical computing
- **scikit-learn** - Machine learning for flood prediction

### Database
- **PostgreSQL 15+** - Relational database
- **PostGIS** - Spatial database extender

### Infrastructure
- **Docker + Docker Compose** - Containerization and orchestration
- **Nginx** - Reverse proxy (optional for production)

## 3. System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         FRONTEND (React)                        │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │   Dashboard │  │  Map View   │  │  Satellite Viewer       │  │
│  │  Components │  │  (MapLibre) │  │  (Before/After Slider)  │  │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │   Charts    │  │   AOI       │  │  Layer Control Panel    │  │
│  │  (Recharts) │  │   Drawing   │  │  (Visibility/Opacity)   │  │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ HTTP/WebSocket
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      BACKEND (FastAPI)                          │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                    API Endpoints                        │   │
│  │  /api/location  /api/satellite  /api/flood  /api/export  │   │
│  └──────────────────────────────────────────────────────────┘   │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │  Satellite  │  │   Flood     │  │    Prediction           │  │
│  │  Service    │  │  Detection  │  │    Model (ML)           │  │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │    GIS      │  │  Hydrology  │  │     Task Queue          │  │
│  │  Processing │  │   Analysis  │  │     (Celery)            │  │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
              ┌───────────────┼───────────────┐
              ▼               ▼               ▼
       ┌────────────┐  ┌────────────┐  ┌────────────┐
       │ PostgreSQL │  │   Redis    │  │   File     │
       │  + PostGIS │  │  (Broker)  │  │  Storage   │
       └────────────┘  └────────────┘  └────────────┘
                              │
                              ▼
       ┌──────────────────────────────────────────┐
       │         External Data Sources            │
       │  • Copernicus Data Space Ecosystem       │
       │  • STAC APIs (Sentinel Hub, Planetary)   │
       │  • NASA Earthdata (for DEM, rainfall)    │
       │  • OpenStreetMap (rivers, boundaries)    │
       └──────────────────────────────────────────┘
```

## 4. Data Flow

1. **User Input**: Location search or AOI drawing on map
2. **Geocoding**: Convert location name to coordinates/bounds
3. **Satellite Search**: Query STAC API for available imagery
4. **Data Acquisition**: Download selected scenes (async job)
5. **Preprocessing**: Cloud masking, atmospheric correction, terrain correction
6. **Flood Detection**: Apply SAR backscatter thresholding or optical water indices
7. **Historical Analysis**: Compare multiple time periods
8. **Risk Prediction**: Run ML model with terrain, historical, and environmental features
9. **Visualization**: Generate map tiles and serve to frontend
10. **Export**: Package results as GeoTIFF, GeoJSON, PDF report

## 5. Key Design Decisions

### Why Sentinel-1 SAR as Primary?
- All-weather capability (penetrates clouds)
- Sensitive to surface water (low backscatter)
- Regular revisit time (6-12 days)
- Free and open data

### Why FastAPI?
- Automatic OpenAPI documentation
- Async support for I/O operations
- Pydantic integration for validation
- High performance

### Why Celery for Tasks?
- Satellite downloads can take minutes
- Raster processing is CPU-intensive
- Need progress tracking for UX
- Retry logic for failed downloads

### Why MapLibre over Leaflet?
- Better performance for large datasets
- WebGL acceleration
- 3D terrain support
- Active development (Leaflet maintenance mode)

## 6. Security Considerations

- API keys stored in environment variables only
- CORS configured for specific origins
- Input validation on all endpoints
- AOI size limits to prevent abuse
- Rate limiting on expensive operations
- SQL injection prevention via SQLAlchemy
- XSS prevention via React's escaping

## 7. Scalability Notes

- Horizontal scaling via Celery workers
- Redis cluster for high-availability queue
- Database read replicas for analytics
- CDN for static assets and map tiles
- Object storage (S3-compatible) for raster data
