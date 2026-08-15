import React, { useState } from 'react';
import { useAppStore } from '@hooks/useStore';
import type { LocationSearchResult, AOI } from '@/types';

const LocationSearch: React.FC = () => {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<LocationSearchResult[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [showResults, setShowResults] = useState(false);
  const { setCurrentAOI } = useAppStore();

  const handleSearch = async (searchQuery: string) => {
    setQuery(searchQuery);
    if (searchQuery.length < 3) {
      setResults([]);
      return;
    }

    setIsLoading(true);
    try {
      // Simulated search - will connect to backend API
      // In production: const data = await locationService.search(searchQuery);
      setTimeout(() => {
        setResults([
          {
            name: 'Test Location',
            display_name: `${searchQuery}, Test Region`,
            lat: 51.5074,
            lon: -0.1278,
            type: 'city',
            bounding_box: {
              minLat: 51.4,
              maxLat: 51.6,
              minLng: -0.2,
              maxLng: -0.05,
            },
          },
        ]);
        setIsLoading(false);
      }, 500);
    } catch (error) {
      console.error('Search error:', error);
      setIsLoading(false);
    }
  };

  const selectLocation = (result: LocationSearchResult) => {
    const aoi: AOI = {
      name: result.name,
      type: 'rectangle',
      coordinates: [],
      boundingBox: result.bounding_box || {
        minLat: result.lat - 0.1,
        maxLat: result.lat + 0.1,
        minLng: result.lon - 0.1,
        maxLng: result.lon + 0.1,
      },
      area_km2: 100,
    };
    setCurrentAOI(aoi);
    setQuery(result.display_name);
    setShowResults(false);
    setResults([]);
  };

  return (
    <div className="relative">
      <div className="flex gap-2">
        <input
          type="text"
          value={query}
          onChange={(e) => handleSearch(e.target.value)}
          onFocus={() => results.length > 0 && setShowResults(true)}
          placeholder="Search location..."
          className="flex-1 px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-800 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
        {isLoading && (
          <div className="spinner self-center"></div>
        )}
      </div>

      {showResults && results.length > 0 && (
        <div className="absolute top-full left-0 right-0 mt-2 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg z-50 max-h-64 overflow-y-auto">
          {results.map((result, index) => (
            <button
              key={index}
              onClick={() => selectLocation(result)}
              className="w-full px-4 py-3 text-left hover:bg-gray-50 dark:hover:bg-gray-700 border-b border-gray-100 dark:border-gray-700 last:border-b-0"
            >
              <div className="font-medium text-gray-800 dark:text-white">{result.name}</div>
              <div className="text-sm text-gray-500 dark:text-gray-400">{result.display_name}</div>
              <div className="text-xs text-gray-400 dark:text-gray-500 capitalize">{result.type}</div>
            </button>
          ))}
        </div>
      )}
    </div>
  );
};

export default LocationSearch;
