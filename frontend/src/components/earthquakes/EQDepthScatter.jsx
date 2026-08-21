import React from 'react';
import {
  ResponsiveContainer,
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  ZAxis,
  Tooltip,
  CartesianGrid,
} from 'recharts';
import EmptyState from '../common/EmptyState';

export const EQDepthScatter = ({ events, title = 'Magnitude vs Hypocenter Depth' }) => {
  if (!events || events.length === 0) {
    return (
      <div className="card">
        <h3 className="card-title" style={{ marginBottom: '1rem' }}>{title}</h3>
        <EmptyState message="No earthquake events data available for depth scatter plot." />
      </div>
    );
  }

  const data = events.map((e) => ({
    magnitude: e.magnitude,
    depth: e.depth_km,
    place: e.place || 'Unknown location',
    id: e.event_id,
  }));

  return (
    <div className="card">
      <div className="card-header">
        <h3 className="card-title">{title}</h3>
        <span style={{ fontSize: '0.875rem', color: 'var(--text-subtle)' }}>Depth in Kilometers vs Richter Magnitude</span>
      </div>

      <div style={{ width: '100%', height: 320 }}>
        <ResponsiveContainer width="100%" height="100%">
          <ScatterChart margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
            <XAxis
              type="number"
              dataKey="magnitude"
              name="Magnitude"
              stroke="#94a3b8"
              tick={{ fontSize: 12 }}
              domain={['dataMin - 0.5', 'dataMax + 0.5']}
            />
            <YAxis
              type="number"
              dataKey="depth"
              name="Focal Depth (km)"
              stroke="#94a3b8"
              tick={{ fontSize: 12 }}
              reversed
            />
            <ZAxis range={[30, 150]} />
            <Tooltip
              cursor={{ strokeDasharray: '3 3' }}
              contentStyle={{ backgroundColor: '#1e293b', borderColor: '#334155', borderRadius: '0.5rem', color: '#f8fafc' }}
              formatter={(val, name) => [name === 'Magnitude' ? `${val}` : `${val} km`, name]}
            />
            <Scatter name="Earthquake Events" data={data} fill="#f43f5e" opacity={0.7} />
          </ScatterChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

export default EQDepthScatter;
