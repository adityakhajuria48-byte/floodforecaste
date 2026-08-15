import React from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, AreaChart, Area } from 'recharts';

const TimeSeriesChart: React.FC = () => {
  // Mock data - in production this would come from the backend
  const data = [
    { date: '2024-01', water: 12.5, flood: 0 },
    { date: '2024-02', water: 13.2, flood: 0 },
    { date: '2024-03', water: 15.8, flood: 2.1 },
    { date: '2024-04', water: 18.4, flood: 5.6 },
    { date: '2024-05', water: 22.1, flood: 8.9 },
    { date: '2024-06', water: 19.5, flood: 4.2 },
    { date: '2024-07', water: 16.3, flood: 1.5 },
    { date: '2024-08', water: 14.8, flood: 0 },
    { date: '2024-09', water: 13.9, flood: 0 },
    { date: '2024-10', water: 15.2, flood: 0.8 },
    { date: '2024-11', water: 17.6, flood: 3.4 },
    { date: '2024-12', water: 14.5, flood: 0 },
  ];

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4">
      <h3 className="font-semibold text-gray-800 dark:text-white mb-4">Water Extent Over Time</h3>
      <div className="h-48">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={data}>
            <defs>
              <linearGradient id="colorWater" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.8} />
                <stop offset="95%" stopColor="#3b82f6" stopOpacity={0.1} />
              </linearGradient>
              <linearGradient id="colorFlood" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#ef4444" stopOpacity={0.8} />
                <stop offset="95%" stopColor="#ef4444" stopOpacity={0.1} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#374151" opacity={0.3} />
            <XAxis 
              dataKey="date" 
              tick={{ fontSize: 10 }}
              stroke="#6b7280"
            />
            <YAxis 
              tick={{ fontSize: 10 }}
              stroke="#6b7280"
              label={{ value: 'km²', angle: -90, position: 'insideLeft', fontSize: 10 }}
            />
            <Tooltip 
              contentStyle={{ 
                backgroundColor: '#1f2937', 
                border: 'none', 
                borderRadius: '8px',
                color: '#fff',
                fontSize: '12px'
              }}
            />
            <Area 
              type="monotone" 
              dataKey="water" 
              stroke="#3b82f6" 
              fillOpacity={1} 
              fill="url(#colorWater)"
              name="Water Extent"
            />
            <Area 
              type="monotone" 
              dataKey="flood" 
              stroke="#ef4444" 
              fillOpacity={1} 
              fill="url(#colorFlood)"
              name="Flood Extent"
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
      <div className="mt-3 flex justify-center gap-4 text-xs">
        <div className="flex items-center gap-1">
          <div className="w-3 h-3 bg-blue-500 rounded"></div>
          <span className="text-gray-600 dark:text-gray-400">Water Extent</span>
        </div>
        <div className="flex items-center gap-1">
          <div className="w-3 h-3 bg-red-500 rounded"></div>
          <span className="text-gray-600 dark:text-gray-400">Flood Extent</span>
        </div>
      </div>
    </div>
  );
};

export default TimeSeriesChart;
