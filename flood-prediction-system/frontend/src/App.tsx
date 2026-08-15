import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Dashboard from '@pages/Dashboard';
import SatelliteViewer from '@pages/SatelliteViewer';
import AnalysisReport from '@pages/AnalysisReport';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/viewer" element={<SatelliteViewer />} />
        <Route path="/report/:jobId" element={<AnalysisReport />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
