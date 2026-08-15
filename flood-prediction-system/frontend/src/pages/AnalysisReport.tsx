import React from 'react';
import { useParams } from 'react-router-dom';

const AnalysisReport: React.FC = () => {
  const { jobId } = useParams<{ jobId: string }>();

  return (
    <div className="h-screen w-screen bg-white dark:bg-gray-900 overflow-y-auto">
      <header className="sticky top-0 h-16 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between px-8 z-10">
        <h1 className="text-2xl font-bold text-gray-800 dark:text-white">Flood Analysis Report</h1>
        <div className="flex gap-4">
          <button className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700">
            Download PDF
          </button>
          <a href="/" className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600">
            Back to Dashboard
          </a>
        </div>
      </header>

      <main className="p-8 max-w-6xl mx-auto space-y-8">
        <section className="bg-gray-50 dark:bg-gray-800 rounded-lg p-6">
          <h2 className="text-lg font-semibold mb-4">Analysis Summary</h2>
          <div className="grid grid-cols-4 gap-4">
            <div className="text-center p-4 bg-white dark:bg-gray-700 rounded-lg">
              <div className="text-3xl font-bold text-blue-500">--</div>
              <div className="text-sm text-gray-500 dark:text-gray-400">Flooded Area (km²)</div>
            </div>
            <div className="text-center p-4 bg-white dark:bg-gray-700 rounded-lg">
              <div className="text-3xl font-bold text-orange-500">--</div>
              <div className="text-sm text-gray-500 dark:text-gray-400">Risk Level</div>
            </div>
            <div className="text-center p-4 bg-white dark:bg-gray-700 rounded-lg">
              <div className="text-3xl font-bold text-green-500">--</div>
              <div className="text-sm text-gray-500 dark:text-gray-400">Confidence</div>
            </div>
            <div className="text-center p-4 bg-white dark:bg-gray-700 rounded-lg">
              <div className="text-3xl font-bold text-purple-500">--</div>
              <div className="text-sm text-gray-500 dark:text-gray-400">Historical Events</div>
            </div>
          </div>
        </section>

        <section className="space-y-4">
          <h2 className="text-lg font-semibold">Methodology</h2>
          <div className="prose dark:prose-invert">
            <p>
              This analysis uses Sentinel-1 SAR data for flood detection through backscatter thresholding,
              combined with terrain analysis and historical flood patterns for risk prediction.
            </p>
            <ul>
              <li>Sentinel-1 GRD products with VV/VH polarization</li>
              <li>Backscatter threshold: -20 dB (configurable)</li>
              <li>Minimum connected component size: 100 pixels</li>
              <li>Permanent water masking applied</li>
            </ul>
          </div>
        </section>

        <section className="space-y-4">
          <h2 className="text-lg font-semibold">Limitations</h2>
          <div className="p-4 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg">
            <p className="text-sm text-yellow-800 dark:text-yellow-200">
              <strong>Important:</strong> Flood predictions are model-based estimates and should not be used
              as the sole basis for emergency decisions. Always consult official flood warnings and local authorities.
            </p>
          </div>
        </section>
      </main>
    </div>
  );
};

export default AnalysisReport;
