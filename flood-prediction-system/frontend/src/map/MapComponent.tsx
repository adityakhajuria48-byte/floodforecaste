import React, { useEffect, useRef } from 'react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { useAppStore } from '@hooks/useStore';

const MapComponent: React.FC = () => {
  const mapRef = useRef<HTMLDivElement>(null);
  const leafletMap = useRef<L.Map | null>(null);
  const { currentAOI, floodResult, layers, mapState, updateMapState } = useAppStore();

  useEffect(() => {
    if (!mapRef.current || leafletMap.current) return;

    // Initialize map
    leafletMap.current = L.map(mapRef.current, {
      center: [mapState.center.lat, mapState.center.lng],
      zoom: mapState.zoom,
      zoomControl: false,
      attributionControl: false,
    });

    // Add zoom control in custom position
    L.control.zoom({ position: 'bottomright' }).addTo(leafletMap.current);

    // Add base layer (OSM)
    const osmLayer = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 19,
      attribution: '© OpenStreetMap contributors',
    }).addTo(leafletMap.current);

    // Satellite layer
    const satelliteLayer = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
      maxZoom: 19,
      attribution: '© ESRI',
    });

    // Dark matter layer
    const darkLayer = L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
      maxZoom: 19,
      attribution: '© CartoDB',
    });

    // Store layers for toggling
    (leafletMap.current as any).baseLayers = {
      osm: osmLayer,
      satellite: satelliteLayer,
      dark: darkLayer,
    };

    // Map event listeners
    leafletMap.current.on('moveend', () => {
      if (leafletMap.current) {
        const center = leafletMap.current.getCenter();
        updateMapState({
          center: { lat: center.lat, lng: center.lng },
          zoom: leafletMap.current.getZoom(),
        });
      }
    });

    return () => {
      if (leafletMap.current) {
        leafletMap.current.remove();
        leafletMap.current = null;
      }
    };
  }, []);

  // Handle basemap changes
  useEffect(() => {
    if (!leafletMap.current) return;
    
    const map = leafletMap.current;
    Object.values((map as any).baseLayers || {}).forEach((layer: L.TileLayer) => {
      map.removeLayer(layer);
    });

    const selectedLayer = (map as any).baseLayers?.[mapState.basemap];
    if (selectedLayer) {
      selectedLayer.addTo(map);
    }
  }, [mapState.basemap]);

  // Handle AOI display
  useEffect(() => {
    if (!leafletMap.current || !currentAOI) return;

    const map = leafletMap.current;
    
    // Clear existing AOI layers
    map.eachLayer((layer) => {
      if ((layer as any).isAOI) {
        map.removeLayer(layer);
      }
    });

    // Draw AOI rectangle
    const bounds = [
      [currentAOI.boundingBox.minLat, currentAOI.boundingBox.minLng],
      [currentAOI.boundingBox.maxLat, currentAOI.boundingBox.maxLng],
    ];

    const rectangle = L.rectangle(bounds, {
      color: '#3b82f6',
      weight: 2,
      fillOpacity: 0.2,
    }).addTo(map);
    (rectangle as any).isAOI = true;

    // Fit map to AOI
    map.fitBounds(bounds);
  }, [currentAOI]);

  // Handle flood result overlay
  useEffect(() => {
    if (!leafletMap.current || !floodResult?.water_extent_geojson) return;

    const map = leafletMap.current;

    // Clear existing flood layers
    map.eachLayer((layer) => {
      if ((layer as any).isFlood) {
        map.removeLayer(layer);
      }
    });

    // Add flood extent GeoJSON
    const floodLayer = L.geoJSON(floodResult.water_extent_geojson, {
      style: {
        color: '#ef4444',
        weight: 1,
        fillOpacity: 0.5,
      },
    }).addTo(map);
    (floodLayer as any).isFlood = true;
  }, [floodResult]);

  return (
    <div className="w-full h-full">
      <div ref={mapRef} className="w-full h-full" />
      
      {/* Basemap selector */}
      <div className="absolute top-4 left-4 bg-white dark:bg-gray-800 rounded-lg shadow-lg p-2 z-[1000]">
        <div className="text-xs font-medium text-gray-500 dark:text-gray-400 mb-2">Basemap</div>
        <div className="flex gap-1">
          <button
            onClick={() => updateMapState({ basemap: 'osm' })}
            className={`px-2 py-1 text-xs rounded ${
              mapState.basemap === 'osm' 
                ? 'bg-blue-500 text-white' 
                : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300'
            }`}
          >
            OSM
          </button>
          <button
            onClick={() => updateMapState({ basemap: 'satellite' })}
            className={`px-2 py-1 text-xs rounded ${
              mapState.basemap === 'satellite' 
                ? 'bg-blue-500 text-white' 
                : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300'
            }`}
          >
            Satellite
          </button>
          <button
            onClick={() => updateMapState({ basemap: 'dark' })}
            className={`px-2 py-1 text-xs rounded ${
              mapState.basemap === 'dark' 
                ? 'bg-blue-500 text-white' 
                : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300'
            }`}
          >
            Dark
          </button>
        </div>
      </div>
    </div>
  );
};

export default MapComponent;
