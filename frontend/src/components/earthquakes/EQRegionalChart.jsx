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

export const EQRegionalChart = ({ data, title = 'Regional Earthquake Frequency' }) => {
  if (!data || data.length === 0) {
    return (
      <div className="card">
        <h3 className="card-title" style={{ marginBottom: '1rem' }}>{title}</h3>
        <EmptyState message="No regional breakdown data available." />
      </div>
    );
  }

  // Display top 10 regions for clean visual presentation
  const chartData = data.slice(0, 10);

  return (
    <div className="card">
      <div className="card-header">
        <h3 className="card-title">{title}</h3>
        <span style={{ fontSize: '0.875rem', color: 'var(--text-subtle)' }}>Top Regions by Total Seismic Events</span>
      </div>

      <div style={{ width: '100%', height: 320 }}>
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={chartData} layout="vertical" margin={{ top: 10, right: 30, left: 60, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
            <XAxis type="number" stroke="#94a3b8" tick={{ fontSize: 12 }} />
            <YAxis type="category" dataKey="region" stroke="#94a3b8" tick={{ fontSize: 11 }} width={120} />
            <Tooltip
              contentStyle={{ backgroundColor: '#1e293b', borderColor: '#334155', borderRadius: '0.5rem', color: '#f8fafc' }}
              formatter={(val) => [`${val} events`, 'Total Events']}
            />
            <Bar dataKey="total_events" fill="#34d399" radius={[0, 4, 4, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

export default EQRegionalChart;
