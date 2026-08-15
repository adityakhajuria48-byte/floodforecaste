import React, { useState } from 'react';
import { useAppStore } from '@hooks/useStore';
import MapComponent from '@map/MapComponent';
import LocationSearch from '@components/LocationSearch';
import LayerControl from '@components/LayerControl';
import AnalysisPanel from '@components/AnalysisPanel';
import StatisticsPanel from '@components/StatisticsPanel';
import TimeSeriesChart from '@charts/TimeSeriesChart';

const Dashboard: React.FC = () => {
  const { isSidebarOpen, toggleSidebar, isDarkMode, toggleDarkMode } = useAppStore();
  const [showSatelliteViewer, setShowSatelliteViewer] = useState(false);

  return (
    <div className={`h-screen w-screen flex flex-col ${isDarkMode ? 'dark bg-gray-900' : 'bg-gray-50'}`}>
      {/* Header */}
      <header className="h-14 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between px-4 shrink-0">
        <div className="flex items-center gap-4">
          <button
            onClick={toggleSidebar}
            className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
            </svg>
          </button>
          <div className="flex items-center gap-2">
            <svg className="w-8 h-8 text-blue-500" fill="currentColor" viewBox="0 0 24 24">
              <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" />
            </svg>
            <h1 className="text-xl font-bold text-gray-800 dark:text-white">
              Flood Prediction System
            </h1>
          </div>
        </div>

        <div className="flex items-center gap-4">
          <LocationSearch />
          <button
            onClick={() => setShowSatelliteViewer(!showSatelliteViewer)}
            className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition"
          >
            Satellite Viewer
          </button>
          <button
            onClick={toggleDarkMode}
            className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700"
          >
            {isDarkMode ? '☀️' : '🌙'}
          </button>
        </div>
      </header>

      {/* Main Content */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left Sidebar */}
        <aside
          className={`${
            isSidebarOpen ? 'w-80' : 'w-0'
          } transition-all duration-300 bg-white dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700 overflow-y-auto shrink-0`}
        >
          <div className="p-4 space-y-6">
            <LocationSearch />
            <LayerControl />
            <AnalysisPanel />
          </div>
        </aside>

        {/* Map */}
        <main className="flex-1 relative">
          <MapComponent />
          
          {/* Map Controls Overlay */}
          <div className="absolute top-4 right-4 flex flex-col gap-2">
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-2">
              <div className="text-xs text-gray-500 dark:text-gray-400 mb-1">Scale</div>
              <div className="h-2 w-32 bg-gray-200 dark:bg-gray-700 rounded">
                <div className="h-full w-1/2 bg-blue-500 rounded"></div>
              </div>
            </div>
          </div>
        </main>

        {/* Right Panel - Statistics */}
        <aside className="w-96 bg-white dark:bg-gray-800 border-l border-gray-200 dark:border-gray-700 overflow-y-auto shrink-0">
          <div className="p-4 space-y-6">
            <StatisticsPanel />
            <div className="h-64">
              <TimeSeriesChart />
            </div>
          </div>
        </aside>
      </div>

      {/* Status Bar */}
      <footer className="h-8 bg-gray-100 dark:bg-gray-900 border-t border-gray-200 dark:border-gray-700 flex items-center justify-between px-4 text-xs text-gray-500 dark:text-gray-400 shrink-0">
        <div>Ready</div>
        <div className="flex items-center gap-4">
          <span>EPSG:3857</span>
          <span>© OpenStreetMap contributors</span>
        </div>
      </footer>
    </div>
  );
};

export default Dashboard;
