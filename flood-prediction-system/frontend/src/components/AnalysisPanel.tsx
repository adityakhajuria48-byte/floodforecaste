import React, { useState } from 'react';
import { useAppStore } from '@hooks/useStore';
import { floodService } from '@services/api';

const AnalysisPanel: React.FC = () => {
  const { currentAOI, setProcessingJob, setFloodResult } = useAppStore();
  const [platform, setPlatform] = useState<'Sentinel-1' | 'Sentinel-2'>('Sentinel-1');
  const [startDate, setStartDate] = useState('2024-01-01');
  const [endDate, setEndDate] = useState('2024-12-31');
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  const handleFloodDetection = async () => {
    if (!currentAOI) {
      alert('Please select a location first');
      return;
    }

    setIsAnalyzing(true);
    try {
      // Simulated job - in production this would call the real API
      const mockJobId = `job_${Date.now()}`;
      setProcessingJob({ jobId: mockJobId, status: 'QUEUED', progress: 0 });

      // Simulate progress updates
      for (let i = 0; i <= 100; i += 10) {
        await new Promise(resolve => setTimeout(resolve, 500));
        setProcessingJob({ jobId: mockJobId, status: 'PROCESSING', progress: i });
      }

      // Mock result
      const mockResult = {
        job_id: mockJobId,
        status: 'COMPLETED' as const,
        flooded_area_km2: 45.6,
        flood_percentage: 12.3,
        created_at: new Date().toISOString(),
        statistics: {
          total_aoi_area_km2: 370,
          flooded_area_km2: 45.6,
          flood_percentage: 12.3,
          permanent_water_area_km2: 20.5,
          temporary_flood_area_km2: 25.1,
          risk_distribution: { low: 60, moderate: 25, high: 10, very_high: 5 },
        },
      };

      setFloodResult(mockResult);
      setProcessingJob(null);
    } catch (error) {
      console.error('Flood detection error:', error);
      setProcessingJob(null);
    } finally {
      setIsAnalyzing(false);
    }
  };

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4 space-y-4">
      <h3 className="font-semibold text-gray-800 dark:text-white">Flood Analysis</h3>

      {/* Current AOI Info */}
      {currentAOI ? (
        <div className="p-3 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg">
          <div className="text-sm font-medium text-green-800 dark:text-green-200">
            ✓ Area Selected: {currentAOI.name}
          </div>
          <div className="text-xs text-green-600 dark:text-green-400">
            Area: {currentAOI.area_km2.toFixed(2)} km²
          </div>
        </div>
      ) : (
        <div className="p-3 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg">
          <div className="text-sm text-yellow-800 dark:text-yellow-200">
            ⚠ Please select a location to analyze
          </div>
        </div>
      )}

      {/* Platform Selection */}
      <div>
        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
          Satellite Platform
        </label>
        <select
          value={platform}
          onChange={(e) => setPlatform(e.target.value as 'Sentinel-1' | 'Sentinel-2')}
          className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-800 dark:text-white"
        >
          <option value="Sentinel-1">Sentinel-1 SAR (All-weather)</option>
          <option value="Sentinel-2">Sentinel-2 Optical (Cloud-free only)</option>
        </select>
      </div>

      {/* Date Range */}
      <div className="grid grid-cols-2 gap-2">
        <div>
          <label className="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">
            Start Date
          </label>
          <input
            type="date"
            value={startDate}
            onChange={(e) => setStartDate(e.target.value)}
            className="w-full px-2 py-1.5 border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-gray-800 dark:text-white text-sm"
          />
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">
            End Date
          </label>
          <input
            type="date"
            value={endDate}
            onChange={(e) => setEndDate(e.target.value)}
            className="w-full px-2 py-1.5 border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-gray-800 dark:text-white text-sm"
          />
        </div>
      </div>

      {/* Action Buttons */}
      <button
        onClick={handleFloodDetection}
        disabled={!currentAOI || isAnalyzing}
        className={`w-full py-3 px-4 rounded-lg font-medium transition ${
          !currentAOI || isAnalyzing
            ? 'bg-gray-300 dark:bg-gray-700 cursor-not-allowed'
            : 'bg-blue-500 hover:bg-blue-600 text-white'
        }`}
      >
        {isAnalyzing ? (
          <span className="flex items-center justify-center gap-2">
            <div className="spinner w-4 h-4"></div>
            Processing...
          </span>
        ) : (
          'Run Flood Detection'
        )}
      </button>

      <div className="pt-2 border-t border-gray-200 dark:border-gray-700">
        <button
          disabled={!currentAOI}
          className="w-full py-2 px-4 rounded-lg font-medium bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 text-gray-700 dark:text-gray-300 transition disabled:opacity-50"
        >
          Historical Analysis
        </button>
      </div>

      <button
        disabled={!currentAOI}
        className="w-full py-2 px-4 rounded-lg font-medium bg-purple-100 dark:bg-purple-900/30 hover:bg-purple-200 dark:hover:bg-purple-900/50 text-purple-700 dark:text-purple-300 transition disabled:opacity-50"
      >
        Predict Flood Risk
      </button>
    </div>
  );
};

export default AnalysisPanel;
