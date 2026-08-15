import { create } from 'zustand';
import type { AOI, MapState, LayerConfig, FloodDetectionResult, PredictionResult } from '@/types';

interface AppState {
  // AOI State
  currentAOI: AOI | null;
  setCurrentAOI: (aoi: AOI | null) => void;

  // Map State
  mapState: MapState;
  updateMapState: (state: Partial<MapState>) => void;

  // Layers
  layers: LayerConfig[];
  toggleLayer: (layerId: string) => void;
  setLayerOpacity: (layerId: string, opacity: number) => void;
  addLayer: (layer: LayerConfig) => void;
  removeLayer: (layerId: string) => void;

  // Analysis Results
  floodResult: FloodDetectionResult | null;
  setFloodResult: (result: FloodDetectionResult | null) => void;

  predictionResult: PredictionResult | null;
  setPredictionResult: (prediction: PredictionResult | null) => void;

  // UI State
  isSidebarOpen: boolean;
  toggleSidebar: () => void;

  isDarkMode: boolean;
  toggleDarkMode: () => void;

  // Processing State
  processingJob: { jobId: string; status: string; progress: number } | null;
  setProcessingJob: (job: { jobId: string; status: string; progress: number } | null) => void;
}

export const useAppStore = create<AppState>((set) => ({
  // AOI State
  currentAOI: null,
  setCurrentAOI: (aoi) => set({ currentAOI: aoi }),

  // Map State - Default to a neutral view
  mapState: {
    center: { lat: 20, lng: 0 },
    zoom: 3,
    bearing: 0,
    pitch: 0,
    basemap: 'osm',
  },
  updateMapState: (state) =>
    set((appState) => ({
      mapState: { ...appState.mapState, ...state },
    })),

  // Layers - Default layer configuration
  layers: [
    {
      id: 'basemap',
      name: 'Base Map',
      type: 'raster',
      visible: true,
      opacity: 1,
    },
    {
      id: 'flood_extent',
      name: 'Flood Extent',
      type: 'vector',
      visible: true,
      opacity: 0.7,
      color: '#3b82f6',
    },
    {
      id: 'risk_map',
      name: 'Risk Map',
      type: 'heatmap',
      visible: false,
      opacity: 0.6,
    },
    {
      id: 'historical_floods',
      name: 'Historical Floods',
      type: 'vector',
      visible: false,
      opacity: 0.5,
      color: '#ef4444',
    },
    {
      id: 'rivers',
      name: 'Rivers',
      type: 'vector',
      visible: true,
      opacity: 0.8,
      color: '#60a5fa',
    },
  ],
  toggleLayer: (layerId) =>
    set((state) => ({
      layers: state.layers.map((layer) =>
        layer.id === layerId ? { ...layer, visible: !layer.visible } : layer
      ),
    })),
  setLayerOpacity: (layerId, opacity) =>
    set((state) => ({
      layers: state.layers.map((layer) =>
        layer.id === layerId ? { ...layer, opacity } : layer
      ),
    })),
  addLayer: (layer) =>
    set((state) => ({
      layers: [...state.layers, layer],
    })),
  removeLayer: (layerId) =>
    set((state) => ({
      layers: state.layers.filter((layer) => layer.id !== layerId),
    })),

  // Analysis Results
  floodResult: null,
  setFloodResult: (result) => set({ floodResult: result }),

  predictionResult: null,
  setPredictionResult: (prediction) => set({ predictionResult: prediction }),

  // UI State
  isSidebarOpen: true,
  toggleSidebar: () => set((state) => ({ isSidebarOpen: !state.isSidebarOpen })),

  isDarkMode: false,
  toggleDarkMode: () => set((state) => ({ isDarkMode: !state.isDarkMode })),

  // Processing State
  processingJob: null,
  setProcessingJob: (job) => set({ processingJob: job }),
}));
