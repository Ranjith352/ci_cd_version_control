import React from 'react';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
} from 'recharts';
import EmptyState from '../common/EmptyState';

export const EQMagnitudeChart = ({ data, title = 'Earthquake Magnitude Category Distribution' }) => {
  if (!data || data.length === 0) {
    return (
      <div className="card">
        <h3 className="card-title" style={{ marginBottom: '1rem' }}>{title}</h3>
        <EmptyState message="No earthquake magnitude breakdown data available." />
      </div>
    );
  }

  return (
    <div className="card">
      <div className="card-header">
        <h3 className="card-title">{title}</h3>
        <span style={{ fontSize: '0.875rem', color: 'var(--text-subtle)' }}>Richter Analytical Tiers</span>
      </div>

      <div style={{ width: '100%', height: 320 }}>
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
            <XAxis dataKey="magnitude_category" stroke="#94a3b8" tick={{ fontSize: 12 }} />
            <YAxis stroke="#94a3b8" tick={{ fontSize: 12 }} />
            <Tooltip
              contentStyle={{ backgroundColor: '#1e293b', borderColor: '#334155', borderRadius: '0.5rem', color: '#f8fafc' }}
              formatter={(val) => [`${val} events`, 'Event Count']}
            />
            <Bar dataKey="event_count" fill="#818cf8" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

export default EQMagnitudeChart;
