import React from 'react';
import { MapContainer, TileLayer, CircleMarker, Popup } from 'react-leaflet';
import { formatDateTime } from '../../utils/formatters';
import EmptyState from '../common/EmptyState';

export const EQMap = ({ events, maxMarkers = 500, title = 'Global Seismic Epicenter Map' }) => {
  if (!events || events.length === 0) {
    return (
      <div className="card">
        <h3 className="card-title" style={{ marginBottom: '1rem' }}>{title}</h3>
        <EmptyState message="No valid earthquake spatial coordinates to display on map." />
      </div>
    );
  }

  // Filter valid geographic coordinates and limit max rendered markers
  const validEvents = events
    .filter(
      (e) =>
        e.latitude !== null &&
        e.longitude !== null &&
        !isNaN(e.latitude) &&
        !isNaN(e.longitude) &&
        e.latitude >= -90 &&
        e.latitude <= 90 &&
        e.longitude >= -180 &&
        e.longitude <= 180
    )
    .slice(0, maxMarkers);

  if (validEvents.length === 0) {
    return (
      <div className="card">
        <h3 className="card-title" style={{ marginBottom: '1rem' }}>{title}</h3>
        <EmptyState message="No earthquake events found within valid geographical boundaries." />
      </div>
    );
  }

  // Calculate center coordinate
  const centerLat = validEvents[0].latitude;
  const centerLng = validEvents[0].longitude;

  return (
    <div className="card">
      <div className="card-header">
        <h3 className="card-title">{title}</h3>
        <span style={{ fontSize: '0.875rem', color: 'var(--text-subtle)' }}>
          Displaying {validEvents.length} of {events.length} seismic epicenters
        </span>
      </div>

      <MapContainer
        center={[centerLat, centerLng]}
        zoom={3}
        scrollWheelZoom={false}
        className="leaflet-container"
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        {validEvents.map((e) => {
          const mag = e.magnitude || 2.5;
          const radius = Math.max(4, Math.min(20, mag * 2.5));
          let color = '#38bdf8';
          if (mag >= 6.0) color = '#e11d48';
          else if (mag >= 5.0) color = '#f43f5e';
          else if (mag >= 4.0) color = '#fb923c';
          else if (mag >= 3.0) color = '#fbbf24';

          return (
            <CircleMarker
              key={e.event_id}
              center={[e.latitude, e.longitude]}
              radius={radius}
              pathOptions={{ fillColor: color, color: '#ffffff', weight: 1, fillOpacity: 0.7 }}
            >
              <Popup>
                <div style={{ color: '#0f172a', fontSize: '0.875rem', lineHeight: '1.4' }}>
                  <div style={{ fontWeight: 700, fontSize: '1rem', color: color, marginBottom: '0.25rem' }}>
                    Magnitude {mag} ({e.magnitude_category || 'Seismic'})
                  </div>
                  <div><strong>Place:</strong> {e.place || 'Unknown'}</div>
                  <div><strong>Region:</strong> {e.region || 'N/A'}</div>
                  <div><strong>Depth:</strong> {e.depth_km} km</div>
                  <div><strong>Time:</strong> {formatDateTime(e.event_time)}</div>
                  {e.tsunami === 1 && (
                    <div style={{ color: '#e11d48', fontWeight: 700, marginTop: '0.25rem' }}>
                      ⚠️ Tsunami Warning Issued
                    </div>
                  )}
                </div>
              </Popup>
            </CircleMarker>
          );
        })}
      </MapContainer>
    </div>
  );
};

export default EQMap;
