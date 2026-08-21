import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Layout from './components/layout/Layout';
import Dashboard from './pages/Dashboard';
import AirQuality from './pages/AirQuality';
import Earthquakes from './pages/Earthquakes';

export function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Layout pageTitle="Environmental Intelligence Overview" />}>
          <Route index element={<Dashboard />} />
        </Route>
        <Route path="/air-quality" element={<Layout pageTitle="Air Quality Intelligence" />}>
          <Route index element={<AirQuality />} />
        </Route>
        <Route path="/earthquakes" element={<Layout pageTitle="Earthquake Hazards Intelligence" />}>
          <Route index element={<Earthquakes />} />
        </Route>
      </Routes>
    </Router>
  );
}

export default App;
