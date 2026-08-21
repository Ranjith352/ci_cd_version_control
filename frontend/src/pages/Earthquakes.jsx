import React, { useState, useEffect } from 'react';
import { Activity, ShieldAlert, Globe, Compass } from 'lucide-react';
import api from '../services/api';
import useFlowStatus from '../hooks/useFlowStatus';
import EQForm from '../components/earthquakes/EQForm';
import EQMagnitudeChart from '../components/earthquakes/EQMagnitudeChart';
import EQDepthScatter from '../components/earthquakes/EQDepthScatter';
import EQRegionalChart from '../components/earthquakes/EQRegionalChart';
import EQMap from '../components/earthquakes/EQMap';
import KPICard from '../components/common/KPICard';
import StatusBadge from '../components/common/StatusBadge';
import LoadingSpinner from '../components/common/LoadingSpinner';
import ErrorAlert from '../components/common/ErrorAlert';
import EmptyState from '../components/common/EmptyState';
import { formatNumber } from '../utils/formatters';

export const Earthquakes = () => {
  const [activeFlowRunId, setActiveFlowRunId] = useState(null);
  const [triggerLoading, setTriggerLoading] = useState(false);
  const [triggerError, setTriggerError] = useState(null);

  // Visualization filter state
  const [minMagFilter, setMinMagFilter] = useState('2.5');
  const [limitFilter, setLimitFilter] = useState('1000');

  // Visualization data state
  const [vizData, setVizData] = useState(null);
  const [vizLoading, setVizLoading] = useState(false);
  const [vizError, setVizError] = useState(null);

  // Poll status hook
  const { status, message, isPolling, error: flowError } = useFlowStatus(activeFlowRunId, {
    onCompleted: () => {
      fetchEarthquakeData();
    },
  });

  const fetchEarthquakeData = async () => {
    setVizLoading(true);
    setVizError(null);
    try {
      const res = await api.getEarthquakeVisualization({
        min_magnitude: parseFloat(minMagFilter || 2.5),
        limit: parseInt(limitFilter || 1000, 10),
      });
      setVizData(res);
    } catch (err) {
      setVizError(err.message || 'Failed to fetch earthquake visualization data.');
    } finally {
      setVizLoading(false);
    }
  };

  useEffect(() => {
    fetchEarthquakeData();
  }, [minMagFilter, limitFilter]);

  const handleFormSubmit = async (formData) => {
    setTriggerLoading(true);
    setTriggerError(null);
    try {
      const res = await api.triggerUSGS(formData);
      setActiveFlowRunId(res.flow_run_id);
      if (formData.min_magnitude) setMinMagFilter(formData.min_magnitude);
      if (formData.limit) setLimitFilter(formData.limit);
    } catch (err) {
      setTriggerError(err.message || 'Failed to trigger USGS earthquake pipeline.');
    } finally {
      setTriggerLoading(false);
    }
  };

  const calculateKPIs = () => {
    if (!vizData || !vizData.events || vizData.events.length === 0) {
      return { total: 0, minMag: 'N/A', maxMag: 'N/A', avgDepth: 'N/A' };
    }
    const events = vizData.events;
    const depths = events.map((e) => e.depth_km).filter((d) => d !== null && d !== undefined);
    const avgDepth = depths.length > 0 ? depths.reduce((a, b) => a + b, 0) / depths.length : 0;
    return {
      total: vizData.total_events || events.length,
      minMag: formatNumber(vizData.min_magnitude, 1),
      maxMag: formatNumber(vizData.max_magnitude, 1),
      avgDepth: `${formatNumber(avgDepth, 1)} km`,
    };
  };

  const kpis = calculateKPIs();

  return (
    <div>
      <div style={{ marginBottom: '1.5rem' }}>
        <h2 style={{ fontSize: '1.5rem', fontWeight: 700 }}>Earthquake Hazard Intelligence</h2>
        <p style={{ color: 'var(--text-muted)', fontSize: '0.875rem' }}>
          USGS GeoJSON API pipeline triggering, Prefect status polling, Richter magnitude tiers, and epicenter spatial mapping.
        </p>
      </div>

      <ErrorAlert message={triggerError || flowError || vizError} />

      {/* Input Form */}
      <EQForm onSubmit={handleFormSubmit} isLoading={triggerLoading || isPolling} onReset={fetchEarthquakeData} />

      {/* Pipeline Status Monitoring Container */}
      {activeFlowRunId && (
        <div className="card" style={{ borderColor: 'var(--danger)', borderWidth: '1px' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '1rem' }}>
            <div>
              <div style={{ fontSize: '0.875rem', color: 'var(--text-muted)', fontWeight: 500 }}>
                Active Prefect Flow Run: <code style={{ color: 'var(--danger)', fontSize: '0.875rem' }}>{activeFlowRunId}</code>
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
              <label className="form-label">Minimum Magnitude Filter</label>
              <select
                className="form-select"
                value={minMagFilter}
                onChange={(e) => setMinMagFilter(e.target.value)}
              >
                <option value="1.0">≥ 1.0 (All Micro & Minor)</option>
                <option value="2.5">≥ 2.5 (Minor & Above)</option>
                <option value="4.0">≥ 4.0 (Light & Above)</option>
                <option value="5.0">≥ 5.0 (Moderate & Above)</option>
                <option value="6.0">≥ 6.0 (Strong & Major)</option>
              </select>
            </div>

            <div className="form-group" style={{ marginBottom: 0 }}>
              <label className="form-label">Query Record Limit</label>
              <select
                className="form-select"
                value={limitFilter}
                onChange={(e) => setLimitFilter(e.target.value)}
              >
                <option value="250">250 events</option>
                <option value="500">500 events</option>
                <option value="1000">1,000 events</option>
                <option value="2000">2,000 events</option>
              </select>
            </div>
          </div>

          <button className="btn btn-secondary" onClick={fetchEarthquakeData} disabled={vizLoading}>
            <span>Refresh Visuals</span>
          </button>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid-kpi">
        <KPICard title="Total Seismic Events" value={formatNumber(kpis.total, 0)} subtext="Filtered recorded events" icon={Activity} color="var(--danger)" />
        <KPICard title="Max Magnitude Recorded" value={kpis.maxMag} subtext="Richter Scale Value" icon={ShieldAlert} color="var(--warning)" />
        <KPICard title="Min Magnitude Filter" value={`≥ ${kpis.minMag}`} subtext="Threshold value" icon={Compass} color="var(--primary)" />
        <KPICard title="Avg Hypocenter Depth" value={kpis.avgDepth} subtext="Km below surface" icon={Globe} color="var(--info)" />
      </div>

      {/* Visualizations & Map */}
      {vizLoading ? (
        <LoadingSpinner message="Querying earthquake hazard data from PostgreSQL..." />
      ) : vizData && vizData.events && vizData.events.length > 0 ? (
        <div>
          <EQMap events={vizData.events} />
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(450px, 1fr))', gap: '1.25rem' }}>
            <EQMagnitudeChart data={vizData.monthly_categories || []} />
            <EQDepthScatter events={vizData.events} />
          </div>
          <EQRegionalChart data={vizData.regional_summary || []} />
        </div>
      ) : (
        <div className="card">
          <EmptyState message="No PostgreSQL earthquake records found matching selected filter criteria." />
        </div>
      )}
    </div>
  );
};

export default Earthquakes;
