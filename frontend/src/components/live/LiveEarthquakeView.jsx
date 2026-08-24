import React from 'react';
import { MapContainer, TileLayer, CircleMarker, Popup } from 'react-leaflet';
import { Activity, MapPin, AlertCircle, Layers } from 'lucide-react';
import 'leaflet/dist/leaflet.css';

export const LiveEarthquakeView = ({ earthquakeData = [] }) => {
  if (!earthquakeData || earthquakeData.length === 0) {
    return (
      <div className="card" style={{ padding: '2rem', textAlign: 'center' }}>
        <Activity size={40} style={{ color: 'var(--text-subtle)', marginBottom: '1rem' }} />
        <h3>Waiting for Live USGS Kafka Stream...</h3>
        <p style={{ color: 'var(--text-subtle)', fontSize: '0.875rem' }}>
          Ensure USGS Producer (`python kafka/producer/usgs_producer.py`) and Consumer are active.
        </p>
      </div>
    );
  }

  const latest = earthquakeData[0] || {};
  const centerLat = latest.latitude || 20.0;
  const centerLon = latest.longitude || 0.0;

  const getMagColor = (mag) => {
    if (mag < 3.0) return '#10b981'; // Green
    if (mag < 4.5) return '#3b82f6'; // Blue
    if (mag < 6.0) return '#f59e0b'; // Amber
    if (mag < 7.0) return '#f97316'; // Orange
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
          background: 'linear-gradient(135deg, rgba(239, 68, 68, 0.08) 0%, rgba(15, 23, 42, 0.6) 100%)',
          borderLeft: '4px solid #ef4444',
        }}
      >
        <div>
          <div style={{ fontSize: '0.85rem', color: 'var(--text-subtle)', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <AlertCircle size={16} /> Latest Event Magnitude
          </div>
          <div style={{ fontSize: '1.75rem', fontWeight: 800, color: getMagColor(latest.magnitude), marginTop: '0.25rem' }}>
            M {latest.magnitude} <span style={{ fontSize: '0.875rem' }}>({latest.magnitude_category || 'Moderate'})</span>
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-subtle)' }}>Type: {latest.magnitude_type || 'mb'}</div>
        </div>

        <div>
          <div style={{ fontSize: '0.85rem', color: 'var(--text-subtle)', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <MapPin size={16} /> Location / Place
          </div>
          <div style={{ fontSize: '1.1rem', fontWeight: 600, marginTop: '0.25rem' }}>{latest.place || 'Global Location'}</div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-subtle)' }}>Region: {latest.region || 'Global'}</div>
        </div>

        <div>
          <div style={{ fontSize: '0.85rem', color: 'var(--text-subtle)', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Layers size={16} /> Focal Depth
          </div>
          <div style={{ fontSize: '1.5rem', fontWeight: 700, marginTop: '0.25rem' }}>{latest.depth_km} km</div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-subtle)' }}>
            Coords: {latest.latitude?.toFixed(2)}°, {latest.longitude?.toFixed(2)}°
          </div>
        </div>

        <div>
          <div style={{ fontSize: '0.85rem', color: 'var(--text-subtle)', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Activity size={16} /> Event Time & Status
          </div>
          <div style={{ fontSize: '1rem', fontWeight: 500, marginTop: '0.25rem' }}>
            {latest.event_time ? new Date(latest.event_time).toLocaleString() : 'Just now'}
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-subtle)' }}>
            Status: {latest.status || 'reviewed'} • Tsunami: {latest.tsunami ? 'YES' : 'NO'}
          </div>
        </div>
      </div>

      {/* Interactive Map */}
      <div className="card">
        <h3 style={{ marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <Activity size={20} color="#ef4444" /> Live Real-Time Earthquake Map Markers
        </h3>
        <div style={{ height: '400px', width: '100%', borderRadius: '12px', overflow: 'hidden' }}>
          <MapContainer center={[centerLat, centerLon]} zoom={3} style={{ height: '100%', width: '100%' }}>
            <TileLayer
              attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            />
            {earthquakeData.map((eq, idx) => {
              if (!eq.latitude || !eq.longitude) return null;
              const radius = Math.max(6, (eq.magnitude || 3) * 3);
              const color = getMagColor(eq.magnitude || 0);

              return (
                <CircleMarker
                  key={eq.event_id || idx}
                  center={[eq.latitude, eq.longitude]}
                  radius={radius}
                  pathOptions={{ color: color, fillColor: color, fillOpacity: 0.6 }}
                >
                  <Popup>
                    <div style={{ color: '#0f172a' }}>
                      <strong style={{ fontSize: '1rem' }}>M {eq.magnitude} Earthquake</strong>
                      <p style={{ margin: '4px 0 0 0', fontSize: '0.85rem' }}>{eq.place}</p>
                      <p style={{ margin: '2px 0 0 0', fontSize: '0.75rem', color: '#64748b' }}>
                        Depth: {eq.depth_km} km | {new Date(eq.event_time).toLocaleString()}
                      </p>
                    </div>
                  </Popup>
                </CircleMarker>
              );
            })}
          </MapContainer>
        </div>
      </div>

      {/* Live Stream Table */}
      <div className="card">
        <h3 style={{ marginBottom: '1rem' }}>Kafka Earthquake Stream ({earthquakeData.length} Recent Events)</h3>
        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.875rem' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid var(--border-color)', color: 'var(--text-subtle)' }}>
                <th style={{ padding: '0.75rem' }}>Event ID</th>
                <th style={{ padding: '0.75rem' }}>Magnitude</th>
                <th style={{ padding: '0.75rem' }}>Category</th>
                <th style={{ padding: '0.75rem' }}>Place</th>
                <th style={{ padding: '0.75rem' }}>Depth</th>
                <th style={{ padding: '0.75rem' }}>Coordinates</th>
                <th style={{ padding: '0.75rem' }}>Event Time</th>
              </tr>
            </thead>
            <tbody>
              {earthquakeData.map((row, idx) => (
                <tr
                  key={row.event_id || idx}
                  style={{
                    borderBottom: '1px solid rgba(255,255,255,0.05)',
                    backgroundColor: idx === 0 ? 'rgba(239, 68, 68, 0.05)' : 'transparent',
                  }}
                >
                  <td style={{ padding: '0.75rem', fontFamily: 'monospace' }}>{row.event_id}</td>
                  <td style={{ padding: '0.75rem', fontWeight: 700, color: getMagColor(row.magnitude) }}>
                    M {row.magnitude}
                  </td>
                  <td style={{ padding: '0.75rem' }}>{row.magnitude_category || 'Minor'}</td>
                  <td style={{ padding: '0.75rem' }}>{row.place}</td>
                  <td style={{ padding: '0.75rem' }}>{row.depth_km} km</td>
                  <td style={{ padding: '0.75rem', color: 'var(--text-subtle)' }}>
                    {row.latitude?.toFixed(2)}°, {row.longitude?.toFixed(2)}°
                  </td>
                  <td style={{ padding: '0.75rem', color: 'var(--text-subtle)' }}>
                    {row.event_time ? new Date(row.event_time).toLocaleTimeString() : 'N/A'}
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

export default LiveEarthquakeView;
