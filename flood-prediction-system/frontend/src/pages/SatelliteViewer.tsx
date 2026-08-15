import React from 'react';

const SatelliteViewer: React.FC = () => {
  return (
    <div className="h-screen w-screen bg-gray-900 text-white">
      <header className="h-14 border-b border-gray-700 flex items-center justify-between px-4">
        <h1 className="text-lg font-semibold">Satellite Image Viewer</h1>
        <a href="/" className="text-blue-400 hover:text-blue-300">← Back to Dashboard</a>
      </header>
      <main className="h-[calc(100vh-56px)] flex items-center justify-center">
        <div className="text-center">
          <h2 className="text-2xl font-bold mb-4">Satellite Comparison Viewer</h2>
          <p className="text-gray-400">Select before/after imagery for flood analysis</p>
          <div className="mt-8 p-6 bg-gray-800 rounded-lg max-w-md mx-auto">
            <p className="text-sm text-gray-400">
              This feature requires satellite data credentials to be configured.
              Please set up your Copernicus or Sentinel Hub API credentials in the .env file.
            </p>
          </div>
        </div>
      </main>
    </div>
  );
};

export default SatelliteViewer;
