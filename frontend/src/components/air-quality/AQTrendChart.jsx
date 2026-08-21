import React from 'react';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
} from 'recharts';
import EmptyState from '../common/EmptyState';

export const AQTrendChart = ({ data, parameter = 'pm25', title = 'Air Quality Concentration Trend' }) => {
  if (!data || data.length === 0) {
    return (
      <div className="card">
        <h3 className="card-title" style={{ marginBottom: '1rem' }}>{title}</h3>
        <EmptyState message="No air quality trend data available for the selected pollutant." />
      </div>
    );
  }

  return (
    <div className="card">
      <div className="card-header">
        <h3 className="card-title">{title} ({parameter.toUpperCase()})</h3>
        <span style={{ fontSize: '0.875rem', color: 'var(--text-subtle)' }}>µg/m³ Daily Average</span>
      </div>

      <div style={{ width: '100%', height: 320 }}>
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
            <XAxis dataKey="date" stroke="#94a3b8" tick={{ fontSize: 12 }} />
            <YAxis stroke="#94a3b8" tick={{ fontSize: 12 }} />
            <Tooltip
              contentStyle={{ backgroundColor: '#1e293b', borderColor: '#334155', borderRadius: '0.5rem', color: '#f8fafc' }}
              formatter={(val) => [`${val} µg/m³`, 'Avg Concentration']}
            />
            <Line
              type="monotone"
              dataKey="avg_concentration"
              stroke="#38bdf8"
              strokeWidth={3}
              dot={{ r: 4, fill: '#38bdf8' }}
              activeDot={{ r: 6 }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

export default AQTrendChart;
