import React from 'react';
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
} from 'recharts';
import { Wind, MapPin, Clock, AlertTriangle } from 'lucide-react';

export const LiveAirQualityView = ({ airQualityData = [] }) => {
  if (!airQualityData || airQualityData.length === 0) {
    return (
      <div className="card" style={{ padding: '2rem', textAlign: 'center' }}>
        <Wind size={40} style={{ color: 'var(--text-subtle)', marginBottom: '1rem' }} />
        <h3>Waiting for Live OpenAQ Kafka Stream...</h3>
        <p style={{ color: 'var(--text-subtle)', fontSize: '0.875rem' }}>
          Ensure OpenAQ Producer (`python kafka/producer/openaq_producer.py`) and Consumer are active.
        </p>
      </div>
    );
  }

  // Format data for Recharts (reverse to get chronological order left-to-right)
  const chartData = [...airQualityData].reverse().map((item) => {
    const timeStr = item.reading_timestamp
      ? new Date(item.reading_timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })
      : 'Now';
    return {
      timestamp: timeStr,
      value: item.value ?? item.normalized_value ?? 0,
      parameter: (item.parameter || 'pm25').toUpperCase(),
      unit: item.unit || 'µg/m³',
      station: item.location_name || item.city || 'Station',
    };
  });

  const latest = airQualityData[0] || {};

  const getAqiColor = (aqi) => {
    if (!aqi) return 'var(--text-subtle)';
    if (aqi <= 50) return '#10b981'; // Green
    if (aqi <= 100) return '#f59e0b'; // Yellow
    if (aqi <= 150) return '#f97316'; // Orange
    return '#ef4444'; // Red
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {/* Top Banner KPI Card */}
      <div
        className="card"
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
          gap: '1.5rem',
          background: 'linear-gradient(135deg, rgba(16, 185, 129, 0.08) 0%, rgba(15, 23, 42, 0.6) 100%)',
          borderLeft: '4px solid var(--primary)',
        }}
      >
        <div>
          <div style={{ fontSize: '0.85rem', color: 'var(--text-subtle)', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <MapPin size={16} /> Location / Station
          </div>
          <div style={{ fontSize: '1.25rem', fontWeight: 600, marginTop: '0.25rem' }}>
            {latest.location_name || latest.city || 'Coimbatore'}
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-subtle)' }}>
            {latest.city}, {latest.country} ({latest.latitude?.toFixed(4)}, {latest.longitude?.toFixed(4)})
          </div>
        </div>

        <div>
          <div style={{ fontSize: '0.85rem', color: 'var(--text-subtle)', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Wind size={16} /> Parameter & Value
          </div>
          <div style={{ fontSize: '1.5rem', fontWeight: 700, color: 'var(--primary)', marginTop: '0.25rem' }}>
            {latest.value ?? 0} <span style={{ fontSize: '0.875rem' }}>{latest.unit || 'µg/m³'}</span>
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-subtle)' }}>
            Pollutant: {(latest.parameter || 'pm25').toUpperCase()}
          </div>
        </div>

        <div>
          <div style={{ fontSize: '0.85rem', color: 'var(--text-subtle)', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <AlertTriangle size={16} /> AQI (US EPA)
          </div>
          <div
            style={{
              fontSize: '1.5rem',
              fontWeight: 700,
              color: getAqiColor(latest.aqi_us_epa),
              marginTop: '0.25rem',
            }}
          >
            {latest.aqi_us_epa ?? 'N/A'}
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-subtle)' }}>Source: {latest.source || 'openaq'}</div>
        </div>

        <div>
          <div style={{ fontSize: '0.85rem', color: 'var(--text-subtle)', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Clock size={16} /> Timestamp
          </div>
          <div style={{ fontSize: '1rem', fontWeight: 500, marginTop: '0.25rem' }}>
            {latest.reading_timestamp ? new Date(latest.reading_timestamp).toLocaleString() : 'Just now'}
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-subtle)' }}>Kafka Topic: air-quality-live</div>
        </div>
      </div>

      {/* Real-Time Live Chart */}
      <div className="card">
        <h3 style={{ marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <Wind size={20} color="var(--primary)" /> Live Air Quality Real-Time Measurement Stream
        </h3>
        <div style={{ width: '100%', height: 320 }}>
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={chartData} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
              <defs>
                <linearGradient id="liveAqGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#10b981" stopOpacity={0.4} />
                  <stop offset="95%" stopColor="#10b981" stopOpacity={0.0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.08)" />
              <XAxis dataKey="timestamp" stroke="var(--text-subtle)" fontSize={12} />
              <YAxis stroke="var(--text-subtle)" fontSize={12} />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#1e293b',
                  borderColor: 'var(--border-color)',
                  borderRadius: '8px',
                  color: '#f8fafc',
                }}
              />
              <Area type="monotone" dataKey="value" stroke="#10b981" strokeWidth={2} fillOpacity={1} fill="url(#liveAqGrad)" />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Stream Table */}
      <div className="card">
        <h3 style={{ marginBottom: '1rem' }}>Kafka Message Stream ({airQualityData.length} Recent Records)</h3>
        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.875rem' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid var(--border-color)', color: 'var(--text-subtle)' }}>
                <th style={{ padding: '0.75rem' }}>ID</th>
                <th style={{ padding: '0.75rem' }}>Station</th>
                <th style={{ padding: '0.75rem' }}>City</th>
                <th style={{ padding: '0.75rem' }}>Parameter</th>
                <th style={{ padding: '0.75rem' }}>Value</th>
                <th style={{ padding: '0.75rem' }}>AQI</th>
                <th style={{ padding: '0.75rem' }}>Timestamp</th>
              </tr>
            </thead>
            <tbody>
              {airQualityData.map((row, idx) => (
                <tr
                  key={row.measurement_id || idx}
                  style={{
                    borderBottom: '1px solid rgba(255,255,255,0.05)',
                    backgroundColor: idx === 0 ? 'rgba(16, 185, 129, 0.05)' : 'transparent',
                  }}
                >
                  <td style={{ padding: '0.75rem', fontFamily: 'monospace' }}>{row.measurement_id}</td>
                  <td style={{ padding: '0.75rem' }}>{row.location_name || 'Coimbatore'}</td>
                  <td style={{ padding: '0.75rem' }}>{row.city || 'Coimbatore'}</td>
                  <td style={{ padding: '0.75rem' }}>{(row.parameter || 'pm25').toUpperCase()}</td>
                  <td style={{ padding: '0.75rem', fontWeight: 600, color: 'var(--primary)' }}>
                    {row.value} {row.unit}
                  </td>
                  <td style={{ padding: '0.75rem', color: getAqiColor(row.aqi_us_epa) }}>{row.aqi_us_epa ?? 'N/A'}</td>
                  <td style={{ padding: '0.75rem', color: 'var(--text-subtle)' }}>
                    {row.reading_timestamp ? new Date(row.reading_timestamp).toLocaleTimeString() : 'N/A'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default LiveAirQualityView;
