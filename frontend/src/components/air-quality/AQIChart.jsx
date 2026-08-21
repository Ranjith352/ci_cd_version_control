import React from 'react';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  Cell,
} from 'recharts';
import { getAQIColor } from '../../utils/formatters';
import EmptyState from '../common/EmptyState';

export const AQIChart = ({ data, title = 'US EPA AQI Sub-index Timeline' }) => {
  if (!data || data.length === 0) {
    return (
      <div className="card">
        <h3 className="card-title" style={{ marginBottom: '1rem' }}>{title}</h3>
        <EmptyState message="No AQI sub-index data available." />
      </div>
    );
  }

  return (
    <div className="card">
      <div className="card-header">
        <h3 className="card-title">{title}</h3>
        <span style={{ fontSize: '0.875rem', color: 'var(--text-subtle)' }}>Max Calculated US EPA AQI</span>
      </div>

      <div style={{ width: '100%', height: 320 }}>
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
            <XAxis dataKey="date" stroke="#94a3b8" tick={{ fontSize: 12 }} />
            <YAxis stroke="#94a3b8" tick={{ fontSize: 12 }} />
            <Tooltip
              contentStyle={{ backgroundColor: '#1e293b', borderColor: '#334155', borderRadius: '0.5rem', color: '#f8fafc' }}
              formatter={(val) => [`${val}`, 'Max AQI']}
            />
            <Bar dataKey="max_aqi" radius={[4, 4, 0, 0]}>
              {data.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={getAQIColor(entry.max_aqi)} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

export default AQIChart;
