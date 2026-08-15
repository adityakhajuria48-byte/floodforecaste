# Flood Prediction System

An AI-powered web-based flood prediction and satellite analysis system that uses Sentinel-1 SAR and Sentinel-2 optical imagery to detect floods, analyze historical patterns, and predict flood risk.

## Features

- **Location Search**: Search by city name, coordinates, address, or draw AOI on map
- **Satellite Data Acquisition**: Automatic retrieval of Sentinel-1/2 imagery from Copernicus Data Space
- **Flood Detection**: SAR backscatter analysis and optical water indices (NDWI/MNDWI)
- **Historical Analysis**: Temporal flood pattern analysis and statistics
- **Risk Prediction**: ML-based flood susceptibility modeling
- **Interactive GIS Map**: Professional map interface with layer controls
- **Export Functions**: Download GeoTIFF, GeoJSON, Shapefile, PNG, PDF reports

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Git

### Installation

1. **Clone the repository**
```bash
cd /workspace/flood-prediction-system
```

2. **Configure environment variables**
```bash
cp .env.example .env
# Edit .env with your credentials (see Configuration section)
```

3. **Start the application**
```bash
docker-compose up -d
```

4. **Access the application**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs

### Stopping the Application

```bash
docker-compose down
```

### Viewing Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f frontend
```

## Configuration

### Required Environment Variables

Copy `.env.example` to `.env` and configure:

```bash
# Copernicus Data Space Ecosystem (FREE account required)
# Register at: https://dataspace.copernicus.eu/
COPEERNICUS_USERNAME=your_username
COPEERNICUS_PASSWORD=your_password

# Database (defaults are fine for local development)
POSTGRES_USER=flood_user
POSTGRES_PASSWORD=change_this_password_in_production
POSTGRES_DB=flood_prediction

# Application
SECRET_KEY=generate_a_random_secret_key_here
```

### Optional Environment Variables

- `SENTINEL_HUB_CLIENT_ID` / `SENTINEL_HUB_CLIENT_SECRET`: Alternative satellite data source
- `NASA_EARTHDATA_USERNAME` / `NASA_EARTHDATA_PASSWORD`: For DEM and rainfall data
- `OPENWEATHERMAP_API_KEY`: For real-time rainfall data
- `MAPBOX_ACCESS_TOKEN`: For Mapbox basemaps

## Project Structure

```
flood-prediction-system/
├── backend/                 # Python FastAPI backend
│   ├── app/
│   │   ├── api/            # REST API endpoints
│   │   ├── core/           # Configuration and utilities
│   │   ├── models/         # SQLAlchemy database models
│   │   ├── schemas/        # Pydantic schemas
│   │   ├── services/       # Business logic services
│   │   ├── satellite/      # Satellite data acquisition
│   │   ├── flood_detection/# Flood detection algorithms
│   │   ├── prediction/     # ML prediction models
│   │   ├── hydrology/      # Hydrological analysis
│   │   └── gis/            # GIS processing utilities
│   ├── tests/              # Backend tests
│   └── requirements.txt    # Python dependencies
├── frontend/               # React TypeScript frontend
│   ├── src/
│   │   ├── components/     # UI components
│   │   ├── pages/          # Page components
│   │   ├── map/            # Map components
│   │   ├── charts/         # Chart components
│   │   ├── services/       # API client
│   │   ├── hooks/          # React hooks
│   │   └── types/          # TypeScript types
│   ├── package.json
│   └── vite.config.ts
├── data/                   # Data storage (mounted volumes)
│   ├── raw/               # Raw satellite data
│   ├── processed/         # Processed data
│   ├── dem/               # Digital elevation models
│   ├── satellite/         # Downloaded imagery
│   └── flood_maps/        # Generated flood maps
├── docker/                 # Docker configurations
├── scripts/                # Utility scripts
├── notebooks/              # Jupyter notebooks for analysis
├── docs/                   # Documentation
├── .env.example           # Environment template
├── docker-compose.yml     # Docker Compose configuration
└── README.md              # This file
```

## API Endpoints

### Location
- `POST /api/location/search` - Search for locations
- `POST /api/location/reverse` - Reverse geocoding
- `POST /api/aoi` - Create area of interest
- `GET /api/aoi/{id}` - Get AOI details

### Satellite
- `POST /api/satellite/search` - Search available imagery
- `POST /api/satellite/download` - Download scene (async job)
- `POST /api/satellite/download/batch` - Batch download

### Flood Analysis
- `POST /api/flood/detect` - Detect flood extent (async job)
- `GET /api/flood/result/{jobId}` - Get detection results
- `POST /api/flood/historical` - Historical analysis
- `POST /api/flood/predict` - Predict flood risk
- `POST /api/flood/flow` - Analyze flood flow direction

### Status & Export
- `GET /api/status/{jobId}` - Get job status
- `POST /api/export` - Export results
- `GET /api/export/report/{jobId}` - Download PDF report

## Technology Stack

### Frontend
- React 18 + TypeScript
- Vite (build tool)
- MapLibre GL JS / Leaflet (mapping)
- Tailwind CSS (styling)
- Recharts (charts)
- Zustand (state management)
- Axios (HTTP client)

### Backend
- Python 3.10+
- FastAPI (web framework)
- SQLAlchemy (ORM)
- Celery + Redis (task queue)
- GDAL/Rasterio (geospatial processing)
- GeoPandas/Shapely (vector data)
- xarray/rioxarray (raster data)
- scikit-learn (machine learning)

### Database
- PostgreSQL 15+ with PostGIS

### Infrastructure
- Docker + Docker Compose
- Nginx (reverse proxy in production)

## Scientific Methodology

### Flood Detection (Sentinel-1 SAR)

1. **Preprocessing**: Terrain correction, radiometric calibration
2. **Backscatter Analysis**: Water surfaces show low backscatter in SAR
3. **Thresholding**: Apply dynamic threshold to identify water pixels
4. **Change Detection**: Compare pre-event and post-event imagery
5. **Filtering**: Remove noise and false positives
6. **Vectorization**: Convert raster to polygon features

### Flood Detection (Sentinel-2 Optical)

1. **Atmospheric Correction**: Convert to surface reflectance
2. **Cloud Masking**: Remove cloudy pixels
3. **Water Indices**:
   - NDWI = (Green - NIR) / (Green + NIR)
   - MNDWI = (Green - SWIR) / (Green + SWIR)
4. **Thresholding**: Classify water vs non-water
5. **Validation**: Cross-check with SAR results when available

### Risk Prediction

The flood risk model considers:
- Historical flood frequency
- Elevation and slope (from DEM)
- Distance to rivers
- Land cover type
- Recent precipitation
- Soil characteristics

Output is a probabilistic risk score (0-1) classified as:
- Low (0-0.25)
- Moderate (0.25-0.5)
- High (0.5-0.75)
- Very High (0.75-1.0)

## Important Notes

### Data Access

- **Copernicus Data Space**: Free account required for Sentinel data
- Registration: https://dataspace.copernicus.eu/
- Free tier includes full access to Sentinel archive

### Limitations

- Flood predictions are **model-based estimates**, not guaranteed forecasts
- SAR data availability depends on satellite revisit time (6-12 days)
- Optical data affected by cloud cover
- Large AOIs may take significant processing time

### Uncertainty Communication

The system clearly distinguishes between:
- **Observed Flood Extent**: Detected from satellite imagery
- **Predicted Flood Risk**: Model-based susceptibility estimate

## Testing

```bash
# Run backend tests
docker-compose exec backend pytest

# Run frontend tests
docker-compose exec frontend npm test

# End-to-end test
# See docs/testing.md for detailed E2E test procedures
```

## Development

### Backend Development

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Development

```bash
cd frontend
npm install
npm run dev
```

## Troubleshooting

### Common Issues

1. **Cannot connect to database**
   - Ensure PostgreSQL container is running: `docker-compose ps`
   - Check database credentials in `.env`

2. **Satellite download fails**
   - Verify Copernicus credentials in `.env`
   - Check network connectivity
   - Review backend logs: `docker-compose logs backend`

3. **Map not loading**
   - Check browser console for errors
   - Ensure frontend can reach backend API
   - Verify CORS settings

4. **Processing jobs stuck**
   - Check Redis container: `docker-compose ps redis`
   - Review Celery worker logs
   - Restart worker: `docker-compose restart worker`

## License

MIT License - see LICENSE file for details

## Contributing

Contributions welcome! Please read our contributing guidelines before submitting PRs.

## Citation

If you use this system in research, please cite appropriately.

## Support

For issues and questions:
- GitHub Issues: Report bugs and feature requests
- Documentation: See /docs directory
- API Docs: http://localhost:8000/docs

---

Built with ❤️ for flood risk management and disaster preparedness
