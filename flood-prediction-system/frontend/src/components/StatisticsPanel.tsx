import React from 'react';
import { useAppStore } from '@hooks/useStore';

const StatisticsPanel: React.FC = () => {
  const { floodResult, predictionResult } = useAppStore();

  if (!floodResult && !predictionResult) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4">
        <h3 className="font-semibold text-gray-800 dark:text-white mb-4">Analysis Results</h3>
        <div className="text-center py-8 text-gray-500 dark:text-gray-400">
          <svg className="w-16 h-16 mx-auto mb-4 opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
          </svg>
          <p>No analysis results yet</p>
          <p className="text-sm mt-1">Run flood detection to see statistics</p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4 space-y-4">
      <h3 className="font-semibold text-gray-800 dark:text-white">Analysis Results</h3>

      {floodResult?.statistics && (
        <>
          <div className="grid grid-cols-2 gap-3">
            <div className="p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
              <div className="text-2xl font-bold text-blue-600 dark:text-blue-400">
                {floodResult.statistics.flooded_area_km2.toFixed(1)}
              </div>
              <div className="text-xs text-gray-600 dark:text-gray-400">Flooded Area (km²)</div>
            </div>
            <div className="p-3 bg-orange-50 dark:bg-orange-900/20 rounded-lg">
              <div className="text-2xl font-bold text-orange-600 dark:text-orange-400">
                {floodResult.statistics.flood_percentage.toFixed(1)}%
              </div>
              <div className="text-xs text-gray-600 dark:text-gray-400">AOI Affected</div>
            </div>
          </div>

          <div className="space-y-2">
            <div className="text-sm font-medium text-gray-700 dark:text-gray-300">Risk Distribution</div>
            <div className="space-y-1">
              <div className="flex items-center gap-2">
                <div className="w-16 text-xs text-gray-500">Low</div>
                <div className="flex-1 h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                  <div 
                    className="h-full bg-green-500 rounded-full"
                    style={{ width: `${floodResult.statistics.risk_distribution.low}%` }}
                  />
                </div>
                <div className="w-10 text-xs text-right">{floodResult.statistics.risk_distribution.low}%</div>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-16 text-xs text-gray-500">Moderate</div>
                <div className="flex-1 h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                  <div 
                    className="h-full bg-yellow-500 rounded-full"
                    style={{ width: `${floodResult.statistics.risk_distribution.moderate}%` }}
                  />
                </div>
                <div className="w-10 text-xs text-right">{floodResult.statistics.risk_distribution.moderate}%</div>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-16 text-xs text-gray-500">High</div>
                <div className="flex-1 h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                  <div 
                    className="h-full bg-orange-500 rounded-full"
                    style={{ width: `${floodResult.statistics.risk_distribution.high}%` }}
                  />
                </div>
                <div className="w-10 text-xs text-right">{floodResult.statistics.risk_distribution.high}%</div>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-16 text-xs text-gray-500">Very High</div>
                <div className="flex-1 h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                  <div 
                    className="h-full bg-red-500 rounded-full"
                    style={{ width: `${floodResult.statistics.risk_distribution.very_high}%` }}
                  />
                </div>
                <div className="w-10 text-xs text-right">{floodResult.statistics.risk_distribution.very_high}%</div>
              </div>
            </div>
          </div>

          <div className="pt-3 border-t border-gray-200 dark:border-gray-700">
            <div className="flex justify-between text-sm">
              <span className="text-gray-600 dark:text-gray-400">Permanent Water</span>
              <span className="font-medium">{floodResult.statistics.permanent_water_area_km2.toFixed(1)} km²</span>
            </div>
            <div className="flex justify-between text-sm mt-1">
              <span className="text-gray-600 dark:text-gray-400">Temporary Flood</span>
              <span className="font-medium">{floodResult.statistics.temporary_flood_area_km2.toFixed(1)} km²</span>
            </div>
          </div>
        </>
      )}

      {predictionResult && (
        <div className="pt-3 border-t border-gray-200 dark:border-gray-700">
          <h4 className="font-medium text-gray-800 dark:text-white mb-2">Risk Prediction</h4>
          <div className={`p-3 rounded-lg ${
            predictionResult.risk_level === 'very_high' ? 'bg-red-100 dark:bg-red-900/30' :
            predictionResult.risk_level === 'high' ? 'bg-orange-100 dark:bg-orange-900/30' :
            predictionResult.risk_level === 'moderate' ? 'bg-yellow-100 dark:bg-yellow-900/30' :
            'bg-green-100 dark:bg-green-900/30'
          }`}>
            <div className="text-lg font-bold capitalize">{predictionResult.risk_level.replace('_', ' ')} Risk</div>
            <div className="text-sm opacity-75">Confidence: {(predictionResult.confidence * 100).toFixed(0)}%</div>
          </div>
        </div>
      )}
    </div>
  );
};

export default StatisticsPanel;
