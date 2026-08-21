import React, { useState, useEffect } from 'react';
import { Wind, Gauge, ShieldAlert, Layers } from 'lucide-react';
import api from '../services/api';
import useFlowStatus from '../hooks/useFlowStatus';
import AQForm from '../components/air-quality/AQForm';
import AQTrendChart from '../components/air-quality/AQTrendChart';
import AQIChart from '../components/air-quality/AQIChart';
import KPICard from '../components/common/KPICard';
import StatusBadge from '../components/common/StatusBadge';
import LoadingSpinner from '../components/common/LoadingSpinner';
import ErrorAlert from '../components/common/ErrorAlert';
import EmptyState from '../components/common/EmptyState';
import { formatNumber, getAQICategory } from '../utils/formatters';

export const AirQuality = () => {
  const [activeFlowRunId, setActiveFlowRunId] = useState(null);
  const [triggerLoading, setTriggerLoading] = useState(false);
  const [triggerError, setTriggerError] = useState(null);

  // Visualization filter state
  const [filterCity, setFilterCity] = useState('Coimbatore');
  const [filterParameter, setFilterParameter] = useState('pm25');

  // Visualization data state
  const [vizData, setVizData] = useState(null);
  const [vizLoading, setVizLoading] = useState(false);
  const [vizError, setVizError] = useState(null);

  // Poll status hook
  const { status, message, isPolling, error: flowError } = useFlowStatus(activeFlowRunId, {
    onCompleted: () => {
      fetchAirQualityData();
    },
  });

  const fetchAirQualityData = async () => {
    setVizLoading(true);
    setVizError(null);
    try {
      const res = await api.getAirQualityVisualization({
        city: filterCity,
        parameter: filterParameter,
      });
      setVizData(res);
    } catch (err) {
      setVizError(err.message || 'Failed to fetch air quality visualization data.');
    } finally {
      setVizLoading(false);
    }
  };

  useEffect(() => {
    fetchAirQualityData();
  }, [filterCity, filterParameter]);

  const handleFormSubmit = async (formData) => {
    setTriggerLoading(true);
    setTriggerError(null);
    try {
      const res = await api.triggerOpenAQ(formData);
      setActiveFlowRunId(res.flow_run_id);
      setFilterCity(formData.city);
    } catch (err) {
      setTriggerError(err.message || 'Failed to trigger OpenAQ pipeline.');
    } finally {
      setTriggerLoading(false);
    }
  };

  const calculateKPIs = () => {
    if (!vizData || !vizData.data || vizData.data.length === 0) {
      return { total: 0, avg: 'N/A', maxAQI: 'N/A', category: 'N/A' };
    }
    const data = vizData.data;
    const total = vizData.total_records || data.length;
    const avg = data.reduce((acc, curr) => acc + (curr.avg_concentration || 0), 0) / data.length;
    const aqiList = data.map((d) => d.max_aqi).filter((v) => v !== null && v !== undefined);
    const maxAQI = aqiList.length > 0 ? Math.max(...aqiList) : null;
    return {
      total: total,
      avg: formatNumber(avg, 2),
      maxAQI: maxAQI !== null ? maxAQI : 'N/A',
      category: getAQICategory(maxAQI),
    };
  };

  const kpis = calculateKPIs();

  return (
    <div>
      <div style={{ marginBottom: '1.5rem' }}>
        <h2 style={{ fontSize: '1.5rem', fontWeight: 700 }}>Air Quality Intelligence</h2>
        <p style={{ color: 'var(--text-muted)', fontSize: '0.875rem' }}>
          OpenAQ v3 API data pipeline triggering, Prefect orchestration status, and US EPA AQI sub-indices.
        </p>
      </div>

      <ErrorAlert message={triggerError || flowError || vizError} />

      {/* Input Form */}
      <AQForm onSubmit={handleFormSubmit} isLoading={triggerLoading || isPolling} onReset={fetchAirQualityData} />

      {/* Pipeline Status Monitoring Container */}
      {activeFlowRunId && (
        <div className="card" style={{ borderColor: 'var(--primary)', borderWidth: '1px' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '1rem' }}>
            <div>
              <div style={{ fontSize: '0.875rem', color: 'var(--text-muted)', fontWeight: 500 }}>
                Active Prefect Flow Run: <code style={{ color: 'var(--primary)', fontSize: '0.875rem' }}>{activeFlowRunId}</code>
              </div>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-subtle)', marginTop: '0.25rem' }}>
                {message || (isPolling ? 'Polling status every 3s...' : 'Flow status updated')}
              </div>
            </div>
            <StatusBadge status={status || 'PENDING'} />
          </div>
        </div>
      )}

      {/* Filter Controls Bar */}
      <div className="card" style={{ padding: '1rem 1.25rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '1rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '1.5rem', flexWrap: 'wrap' }}>
            <div className="form-group" style={{ marginBottom: 0 }}>
              <label className="form-label">City Filter</label>
              <select
                className="form-select"
                value={filterCity}
                onChange={(e) => setFilterCity(e.target.value)}
              >
                <option value="Coimbatore">Coimbatore</option>
                <option value="Chennai">Chennai</option>
                <option value="Delhi">Delhi</option>
              </select>
            </div>

            <div className="form-group" style={{ marginBottom: 0 }}>
              <label className="form-label">Pollutant Parameter</label>
              <select
                className="form-select"
                value={filterParameter}
                onChange={(e) => setFilterParameter(e.target.value)}
              >
                <option value="pm25">PM2.5 (Fine Particulate Matter)</option>
                <option value="pm10">PM10 (Coarse Particulate Matter)</option>
                <option value="no2">NO2 (Nitrogen Dioxide)</option>
                <option value="so2">SO2 (Sulfur Dioxide)</option>
                <option value="o3">O3 (Ozone)</option>
              </select>
            </div>
          </div>

          <button className="btn btn-secondary" onClick={fetchAirQualityData} disabled={vizLoading}>
            <span>Refresh Visuals</span>
          </button>
        </div>
      </div>

      {/* KPI Summary Cards */}
      <div className="grid-kpi">
        <KPICard title="Total Processed Records" value={formatNumber(kpis.total, 0)} subtext="Filtered daily data points" icon={Layers} color="var(--primary)" />
        <KPICard title="Avg Concentration" value={`${kpis.avg} µg/m³`} subtext={`Parameter: ${filterParameter.toUpperCase()}`} icon={Wind} color="var(--secondary)" />
        <KPICard title="Maximum AQI" value={kpis.maxAQI} subtext={`Category: ${kpis.category}`} icon={Gauge} color="var(--warning)" />
        <KPICard title="Pollutant Selected" value={filterParameter.toUpperCase()} subtext="Normalized to µg/m³" icon={ShieldAlert} color="var(--info)" />
      </div>

      {/* Charts */}
      {vizLoading ? (
        <LoadingSpinner message="Querying air quality visualization data from PostgreSQL..." />
      ) : vizData && vizData.data && vizData.data.length > 0 ? (
        <div>
          <AQTrendChart data={vizData.data} parameter={filterParameter} />
          <AQIChart data={vizData.data} />
        </div>
      ) : (
        <div className="card">
          <EmptyState message={`No PostgreSQL air quality data found for city '${filterCity}' and parameter '${filterParameter.toUpperCase()}'.`} />
        </div>
      )}
    </div>
  );
};

export default AirQuality;
