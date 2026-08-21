import React, { useState, useEffect } from 'react';
import { Wind, Activity, Database, Server, ArrowRight, RefreshCw } from 'lucide-react';
import { Link } from 'react-router-dom';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  Legend,
} from 'recharts';
import api from '../services/api';
import KPICard from '../components/common/KPICard';
import LoadingSpinner from '../components/common/LoadingSpinner';
import ErrorAlert from '../components/common/ErrorAlert';
import EmptyState from '../components/common/EmptyState';
import { formatNumber } from '../utils/formatters';

export const Dashboard = () => {
  const [trends, setTrends] = useState([]);
  const [aqCount, setAqCount] = useState(null);
  const [eqCount, setEqCount] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchDashboardData = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const [trendRes, aqRes, eqRes] = await Promise.all([
        api.getTrends(),
        api.getAirQualityVisualization({ city: 'Coimbatore' }),
        api.getEarthquakeVisualization(),
      ]);

      setTrends(trendRes.trends || []);
      setAqCount(aqRes.total_records ?? null);
      setEqCount(eqRes.total_events ?? null);
    } catch (err) {
      setError(err.message || 'Failed to load system dashboard analytics.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboardData();
  }, []);

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
        <div>
          <h2 style={{ fontSize: '1.5rem', fontWeight: 700 }}>Executive Overview</h2>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.875rem' }}>
            Real-time telemetry and database aggregations from OpenAQ and USGS ETL pipelines.
          </p>
        </div>

        <button className="btn btn-secondary" onClick={fetchDashboardData} disabled={isLoading}>
          <RefreshCw size={16} className={isLoading ? 'spin-icon' : ''} />
          <span>Refresh Data</span>
        </button>
      </div>

      <ErrorAlert message={error} onRetry={fetchDashboardData} />

      {/* KPI Cards Grid */}
      <div className="grid-kpi">
        <KPICard
          title="Air Quality Records"
          value={formatNumber(aqCount, 0)}
          subtext="Coimbatore & discovered locations"
          icon={Wind}
          color="var(--primary)"
        />
        <KPICard
          title="Earthquake Hazards"
          value={formatNumber(eqCount, 0)}
          subtext="USGS seismic events recorded"
          icon={Activity}
          color="var(--danger)"
        />
        <KPICard
          title="Pipeline Integration"
          value="Active"
          subtext="Prefect 3.x Orchestration"
          icon={Database}
          color="var(--success)"
        />
        <KPICard
          title="FastAPI Layer"
          value="Online"
          subtext="PostgreSQL data_engineering"
          icon={Server}
          color="var(--secondary)"
        />
      </div>

      {/* Analytics Independent Trend Line Chart */}
      <div className="card">
        <div className="card-header">
          <div>
            <h3 className="card-title">Environmental Cross-Domain Timeseries Analytics</h3>
            <span style={{ fontSize: '0.875rem', color: 'var(--text-subtle)' }}>
              Independent daily PM2.5 averages (µg/m³) vs Earthquake event frequencies
            </span>
          </div>
        </div>

        {isLoading ? (
          <LoadingSpinner message="Fetching timeseries trends from PostgreSQL..." />
        ) : trends.length === 0 ? (
          <EmptyState message="No time-series analytics records available." />
        ) : (
          <div style={{ width: '100%', height: 350 }}>
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={trends} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                <XAxis dataKey="date" stroke="#94a3b8" tick={{ fontSize: 12 }} />
                <YAxis yAxisId="left" stroke="#38bdf8" tick={{ fontSize: 12 }} label={{ value: 'PM2.5 (µg/m³)', angle: -90, position: 'insideLeft', fill: '#38bdf8' }} />
                <YAxis yAxisId="right" orientation="right" stroke="#f43f5e" tick={{ fontSize: 12 }} label={{ value: 'Quake Count', angle: 90, position: 'insideRight', fill: '#f43f5e' }} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#1e293b', borderColor: '#334155', borderRadius: '0.5rem', color: '#f8fafc' }}
                />
                <Legend wrapperStyle={{ paddingTop: '10px' }} />
                <Line yAxisId="left" type="monotone" dataKey="pm25_avg" name="Daily PM2.5 Avg (µg/m³)" stroke="#38bdf8" strokeWidth={2.5} dot={{ r: 3 }} />
                <Line yAxisId="right" type="monotone" dataKey="earthquake_count" name="Daily Quake Count" stroke="#f43f5e" strokeWidth={2.5} dot={{ r: 3 }} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        )}
      </div>

      {/* Navigation Quick Links */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '1.25rem' }}>
        <div className="card" style={{ marginBottom: 0 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1rem' }}>
            <Wind size={24} color="var(--primary)" />
            <h3 className="card-title">Air Quality Dashboard</h3>
          </div>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.875rem', marginBottom: '1.25rem' }}>
            Trigger OpenAQ pipeline, monitor Prefect flow runs, and inspect EPA AQI sub-indices.
          </p>
          <Link to="/air-quality" className="btn btn-secondary" style={{ width: '100%' }}>
            <span>Go to Air Quality</span>
            <ArrowRight size={16} />
          </Link>
        </div>

        <div className="card" style={{ marginBottom: 0 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1rem' }}>
            <Activity size={24} color="var(--danger)" />
            <h3 className="card-title">Earthquake Hazards</h3>
          </div>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.875rem', marginBottom: '1.25rem' }}>
            Trigger USGS earthquake pipeline, monitor flow runs, and analyze hypocenter depth vs magnitude.
          </p>
          <Link to="/earthquakes" className="btn btn-secondary" style={{ width: '100%' }}>
            <span>Go to Earthquakes</span>
            <ArrowRight size={16} />
          </Link>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
