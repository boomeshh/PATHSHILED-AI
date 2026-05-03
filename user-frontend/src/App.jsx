import { Routes, Route } from 'react-router-dom';
import Home from './pages/Home.jsx';
import SubmitReport from './pages/SubmitReport.jsx';
import AIResult from './pages/AIResult.jsx';
import EmergencySOS from './pages/EmergencySOS.jsx';
import PublicDashboard from './pages/PublicDashboard.jsx';

export default function App() {
  return (
    <Routes>
      <Route path="/"              element={<Home />} />
      <Route path="/submit"        element={<SubmitReport />} />
      <Route path="/result/:id"    element={<AIResult />} />
      <Route path="/sos"           element={<EmergencySOS />} />
      <Route path="/public-dashboard" element={<PublicDashboard />} />
    </Routes>
  );
}
