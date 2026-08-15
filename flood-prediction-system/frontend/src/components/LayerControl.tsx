import React from 'react';
import { useAppStore } from '@hooks/useStore';

const LayerControl: React.FC = () => {
  const { layers, toggleLayer, setLayerOpacity } = useAppStore();

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4">
      <h3 className="font-semibold text-gray-800 dark:text-white mb-3">Layers</h3>
      <div className="space-y-3">
        {layers.map((layer) => (
          <div key={layer.id} className="flex items-center gap-3">
            <input
              type="checkbox"
              checked={layer.visible}
              onChange={() => toggleLayer(layer.id)}
              className="w-4 h-4 text-blue-500 rounded focus:ring-blue-500"
            />
            <span className="flex-1 text-sm text-gray-700 dark:text-gray-300">{layer.name}</span>
            {layer.visible && (
              <input
                type="range"
                min="0"
                max="1"
                step="0.1"
                value={layer.opacity}
                onChange={(e) => setLayerOpacity(layer.id, parseFloat(e.target.value))}
                className="w-20 compare-slider"
              />
            )}
          </div>
        ))}
      </div>
    </div>
  );
};

export default LayerControl;
