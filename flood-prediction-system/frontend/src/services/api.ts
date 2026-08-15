import axios from 'axios';
import type {
  LocationSearchResult,
  AOI,
  SatelliteScene,
  FloodDetectionResult,
  HistoricalAnalysis,
  PredictionResult,
  JobStatus,
  ExportOptions,
} from '@/types';

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Location Services
export const locationService = {
  search: async (query: string): Promise<LocationSearchResult[]> => {
    const response = await api.post('/location/search', { query });
    return response.data;
  },

  reverseGeocode: async (lat: number, lng: number): Promise<string> => {
    const response = await api.post('/location/reverse', { lat, lng });
    return response.data.display_name;
  },

  createAOI: async (aoi: Omit<AOI, 'id'>): Promise<AOI> => {
    const response = await api.post('/aoi', aoi);
    return response.data;
  },

  getAOI: async (id: string): Promise<AOI> => {
    const response = await api.get(`/aoi/${id}`);
    return response.data;
  },

  deleteAOI: async (id: string): Promise<void> => {
    await api.delete(`/aoi/${id}`);
  },
};

// Satellite Services
export const satelliteService = {
  search: async (
    aoi: AOI,
    platform: 'Sentinel-1' | 'Sentinel-2',
    startDate: string,
    endDate: string,
    maxCloudCover?: number
  ): Promise<SatelliteScene[]> => {
    const response = await api.post('/satellite/search', {
      aoi,
      platform,
      start_date: startDate,
      end_date: endDate,
      max_cloud_cover: maxCloudCover,
    });
    return response.data;
  },

  download: async (sceneId: string): Promise<JobStatus> => {
    const response = await api.post('/satellite/download', { scene_id: sceneId });
    return response.data;
  },

  downloadBatch: async (sceneIds: string[]): Promise<JobStatus> => {
    const response = await api.post('/satellite/download/batch', { scene_ids: sceneIds });
    return response.data;
  },
};

// Flood Detection Services
export const floodService = {
  detect: async (aoi: AOI, sceneIds: string[], options?: any): Promise<JobStatus> => {
    const response = await api.post('/flood/detect', {
      aoi,
      scene_ids: sceneIds,
      ...options,
    });
    return response.data;
  },

  getResult: async (jobId: string): Promise<FloodDetectionResult> => {
    const response = await api.get(`/flood/result/${jobId}`);
    return response.data;
  },

  getHistorical: async (
    aoi: AOI,
    startDate: string,
    endDate: string
  ): Promise<HistoricalAnalysis> => {
    const response = await api.post('/flood/historical', {
      aoi,
      start_date: startDate,
      end_date: endDate,
    });
    return response.data;
  },

  predict: async (aoi: AOI, detectionResult?: FloodDetectionResult): Promise<JobStatus> => {
    const response = await api.post('/flood/predict', {
      aoi,
      detection_result: detectionResult,
    });
    return response.data;
  },

  getPredictionResult: async (jobId: string): Promise<PredictionResult> => {
    const response = await api.get(`/flood/prediction/${jobId}`);
    return response.data;
  },

  analyzeFlow: async (aoi: AOI, floodExtent: GeoJSON.FeatureCollection): Promise<JobStatus> => {
    const response = await api.post('/flood/flow', {
      aoi,
      flood_extent: floodExtent,
    });
    return response.data;
  },
};

// Job Status Service
export const jobService = {
  getStatus: async (jobId: string): Promise<JobStatus> => {
    const response = await api.get(`/status/${jobId}`);
    return response.data;
  },

  cancelJob: async (jobId: string): Promise<void> => {
    await api.post(`/status/${jobId}/cancel`);
  },
};

// Export Service
export const exportService = {
  export: async (options: ExportOptions, jobId?: string): Promise<Blob> => {
    const response = await api.post('/export', options, {
      responseType: 'blob',
      params: jobId ? { job_id: jobId } : {},
    });
    return response.data;
  },

  downloadReport: async (jobId: string): Promise<Blob> => {
    const response = await api.get(`/export/report/${jobId}`, {
      responseType: 'blob',
    });
    return response.data;
  },
};

// Layer Service
export const layerService = {
  getTileUrl: (layerId: string, z: number, x: number, y: number): string => {
    return `${API_BASE_URL}/layers/${layerId}/tile/${z}/${x}/${y}`;
  },

  getGeoJSON: async (layerId: string): Promise<GeoJSON.FeatureCollection> => {
    const response = await api.get(`/layers/${layerId}/geojson`);
    return response.data;
  },
};

export default api;
