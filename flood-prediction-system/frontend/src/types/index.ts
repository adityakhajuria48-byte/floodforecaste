export interface Coordinates {
  lat: number;
  lng: number;
}

export interface BoundingBox {
  minLat: number;
  maxLat: number;
  minLng: number;
  maxLng: number;
}

export interface AOI {
  id?: string;
  name: string;
  type: 'point' | 'polygon' | 'rectangle';
  coordinates: Coordinates[] | GeoJSON.Polygon | GeoJSON.MultiPolygon;
  boundingBox: BoundingBox;
  area_km2: number;
  created_at?: string;
}

export interface SatelliteScene {
  id: string;
  platform: 'Sentinel-1' | 'Sentinel-2';
  acquisition_date: string;
  cloud_cover?: number;
  polarization?: 'VV' | 'VH' | 'VV+VH';
  product_type: 'GRD' | 'L1C' | 'L2A';
  path?: string;
  url: string;
  bounds: BoundingBox;
}

export interface FloodDetectionResult {
  job_id: string;
  status: 'QUEUED' | 'DOWNLOADING' | 'PROCESSING' | 'ANALYZING' | 'PREDICTING' | 'COMPLETED' | 'FAILED';
  flooded_area_km2?: number;
  flood_percentage?: number;
  water_extent_geojson?: GeoJSON.FeatureCollection;
  risk_map_geojson?: GeoJSON.FeatureCollection;
  statistics?: FloodStatistics;
  error_message?: string;
  created_at: string;
  completed_at?: string;
}

export interface FloodStatistics {
  total_aoi_area_km2: number;
  flooded_area_km2: number;
  flood_percentage: number;
  permanent_water_area_km2: number;
  temporary_flood_area_km2: number;
  risk_distribution: {
    low: number;
    moderate: number;
    high: number;
    very_high: number;
  };
  historical_flood_count?: number;
  max_historical_flood_area_km2?: number;
}

export interface HistoricalAnalysis {
  aoi_id: string;
  date_range: {
    start: string;
    end: string;
  };
  scenes_analyzed: number;
  flood_events: FloodEvent[];
  time_series: TimeSeriesDataPoint[];
  statistics: HistoricalStatistics;
}

export interface FloodEvent {
  id: string;
  detection_date: string;
  flooded_area_km2: number;
  severity: 'low' | 'moderate' | 'high' | 'very_high';
  scene_id: string;
}

export interface TimeSeriesDataPoint {
  date: string;
  water_extent_km2: number;
  flood_extent_km2: number;
  rainfall_mm?: number;
}

export interface HistoricalStatistics {
  total_flood_events: number;
  max_flooded_area_km2: number;
  avg_flooded_area_km2: number;
  flood_frequency_per_year: number;
  seasonal_pattern: {
    spring: number;
    summer: number;
    autumn: number;
    winter: number;
  };
}

export interface PredictionResult {
  risk_level: 'low' | 'moderate' | 'high' | 'very_high';
  probability: number;
  confidence: number;
  contributing_factors: string[];
  risk_map_url?: string;
  recommendations: string[];
}

export interface LayerConfig {
  id: string;
  name: string;
  type: 'raster' | 'vector' | 'heatmap';
  visible: boolean;
  opacity: number;
  url?: string;
  geojson?: GeoJSON.FeatureCollection;
  color?: string;
}

export interface MapState {
  center: Coordinates;
  zoom: number;
  bearing: number;
  pitch: number;
  basemap: 'osm' | 'satellite' | 'terrain' | 'dark';
}

export interface JobStatus {
  job_id: string;
  status: string;
  progress: number;
  message: string;
  result?: any;
  error?: string;
}

export interface LocationSearchResult {
  name: string;
  display_name: string;
  lat: number;
  lon: number;
  type: 'city' | 'town' | 'village' | 'river' | 'address' | 'district';
  bounding_box?: BoundingBox;
}

export interface ExportOptions {
  format: 'geotiff' | 'geojson' | 'shapefile' | 'geopackage' | 'png' | 'pdf' | 'csv';
  layers: string[];
  include_statistics: boolean;
  include_maps: boolean;
}
