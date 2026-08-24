import React, { useState, useEffect, useRef } from 'react';
import { Radio, RefreshCw, AlertCircle, CheckCircle, WifiOff } from 'lucide-react';
import LiveAirQualityView from '../components/live/LiveAirQualityView';
import LiveEarthquakeView from '../components/live/LiveEarthquakeView';
import api from '../services/api';

export const LiveMonitoring = () => {
  const [activeTab, setActiveTab] = useState('all'); // 'all', 'air-quality', 'earthquakes'
  const [connectionStatus, setConnectionStatus] = useState('DISCONNECTED'); // 'CONNECTED', 'DISCONNECTED', 'RECONNECTING'
  const [airQualityEvents, setAirQualityEvents] = useState([]);
  const [earthquakeEvents, setEarthquakeEvents] = useState([]);
  const [healthStatus, setHealthStatus] = useState({ kafka: 'unknown', redis: 'unknown' });
  const [lastUpdated, setLastUpdated] = useState(null);

  const socketRef = useRef(null);
  const reconnectTimeoutRef = useRef(null);
  const backoffRef = useRef(2000); // Initial backoff 2 seconds

  // Fetch REST initial snapshot or fallback polling
  const fetchSnapshot = async () => {
    try {
      const [aqRes, eqRes, healthRes] = await Promise.allSettled([
        api.getLiveAirQuality(),
        api.getLiveEarthquakes(),
        api.getLiveHealth(),
      ]);

      if (aqRes.status === 'fulfilled' && aqRes.value?.records) {
        setAirQualityEvents(aqRes.value.records);
      }
      if (eqRes.status === 'fulfilled' && eqRes.value?.events) {
        setEarthquakeEvents(eqRes.value.events);
      }
      if (healthRes.status === 'fulfilled') {
        setHealthStatus(healthRes.value);
      }
      setLastUpdated(new Date());
    } catch (err) {
      console.warn('Fallback REST snapshot fetch error:', err);
    }
  };

  const connectWebSocket = () => {
    if (socketRef.current && (socketRef.current.readyState === WebSocket.OPEN || socketRef.current.readyState === WebSocket.CONNECTING)) {
      return;
    }

    setConnectionStatus('RECONNECTING');
    const wsUrl = api.getWebSocketUrl();

    try {
      const ws = new WebSocket(wsUrl);
      socketRef.current = ws;

      ws.onopen = () => {
        setConnectionStatus('CONNECTED');
        backoffRef.current = 2000; // Reset backoff delay on successful connection
        console.log('Real-Time WebSocket Connected:', wsUrl);
      };

      ws.onmessage = (event) => {
        try {
          const payload = JSON.parse(event.data);

          if (payload.type === 'SNAPSHOT' || payload.type === 'UPDATE') {
            if (payload.air_quality && payload.air_quality.length > 0) {
              setAirQualityEvents((prev) => {
                const combined = [...payload.air_quality, ...prev];
                // Deduplicate by measurement_id
                const seen = new Set();
                const unique = [];
                for (const item of combined) {
                  const id = item.measurement_id;
                  if (!seen.has(id)) {
                    seen.add(id);
                    unique.push(item);
                  }
                }
                return unique.slice(0, 50);
              });
            }

            if (payload.earthquakes && payload.earthquakes.length > 0) {
              setEarthquakeEvents((prev) => {
                const combined = [...payload.earthquakes, ...prev];
                // Deduplicate by event_id
                const seen = new Set();
                const unique = [];
                for (const item of combined) {
                  const id = item.event_id;
                  if (!seen.has(id)) {
                    seen.add(id);
                    unique.push(item);
                  }
                }
                return unique.slice(0, 50);
              });
            }
            setLastUpdated(new Date());
          }
        } catch (err) {
          console.error('Error parsing WebSocket message:', err);
        }
      };

      ws.onerror = (err) => {
        console.warn('WebSocket error encountered:', err);
        setConnectionStatus('DISCONNECTED');
      };

      ws.onclose = () => {
        setConnectionStatus('DISCONNECTED');
        // Exponential backoff reconnect logic
        const nextDelay = Math.min(backoffRef.current * 1.5, 30000);
        backoffRef.current = nextDelay;

        reconnectTimeoutRef.current = setTimeout(() => {
          connectWebSocket();
        }, nextDelay);
      };
    } catch (e) {
      console.error('Failed to construct WebSocket client:', e);
      setConnectionStatus('DISCONNECTED');
    }
  };

  useEffect(() => {
    fetchSnapshot();
    connectWebSocket();

    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (socketRef.current) {
        socketRef.current.close();
      }
    };
  }, []);

  const handleManualRefresh = () => {
    fetchSnapshot();
    if (connectionStatus !== 'CONNECTED') {
      connectWebSocket();
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {/* Top Header Card */}
      <div
        className="card"
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '1rem',
        }}
      >
        <div>
          <h2 style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Radio size={24} color="var(--primary)" /> Real-Time Kafka & Redis Monitoring
          </h2>
          <p style={{ color: 'var(--text-subtle)', fontSize: '0.875rem', marginTop: '0.25rem' }}>
            Live environmental streaming data pushed from Apache Kafka & Redis via FastAPI WebSockets.
          </p>
        </div>

        {/* Status Indicators */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          {/* Connection Status Badge */}
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem',
              padding: '0.4rem 0.8rem',
              borderRadius: '20px',
              fontSize: '0.85rem',
              fontWeight: 600,
              backgroundColor:
                connectionStatus === 'CONNECTED'
                  ? 'rgba(16, 185, 129, 0.15)'
                  : connectionStatus === 'RECONNECTING'
                  ? 'rgba(245, 158, 11, 0.15)'
                  : 'rgba(239, 68, 68, 0.15)',
              color:
                connectionStatus === 'CONNECTED'
                  ? '#10b981'
                  : connectionStatus === 'RECONNECTING'
                  ? '#f59e0b'
                  : '#ef4444',
              border: `1px solid ${
                connectionStatus === 'CONNECTED'
                  ? 'rgba(16, 185, 129, 0.3)'
                  : connectionStatus === 'RECONNECTING'
                  ? 'rgba(245, 158, 11, 0.3)'
                  : 'rgba(239, 68, 68, 0.3)'
              }`,
            }}
          >
            {connectionStatus === 'CONNECTED' ? (
              <>
                <CheckCircle size={16} /> CONNECTED
              </>
            ) : connectionStatus === 'RECONNECTING' ? (
              <>
                <RefreshCw size={16} className="spin" /> RECONNECTING
              </>
            ) : (
              <>
                <WifiOff size={16} /> DISCONNECTED
              </>
            )}
          </div>

          {/* Infrastructure Health Badge */}
          <div style={{ fontSize: '0.75rem', color: 'var(--text-subtle)' }}>
            Kafka: <strong style={{ color: healthStatus.kafka === 'healthy' ? '#10b981' : '#f59e0b' }}>{healthStatus.kafka}</strong> | Redis: <strong style={{ color: healthStatus.redis === 'healthy' ? '#10b981' : '#f59e0b' }}>{healthStatus.redis}</strong>
          </div>

          {/* Refresh Button */}
          <button
            onClick={handleManualRefresh}
            style={{
              padding: '0.5rem 1rem',
              borderRadius: '6px',
              backgroundColor: 'var(--card-bg)',
              color: 'var(--text-main)',
              border: '1px solid var(--border-color)',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem',
              fontSize: '0.85rem',
            }}
          >
            <RefreshCw size={16} /> Sync
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div style={{ display: 'flex', gap: '0.5rem', borderBottom: '1px solid var(--border-color)', paddingBottom: '0.5rem' }}>
        <button
          onClick={() => setActiveTab('all')}
          style={{
            padding: '0.5rem 1.25rem',
            borderRadius: '6px',
            backgroundColor: activeTab === 'all' ? 'var(--primary)' : 'transparent',
            color: activeTab === 'all' ? '#ffffff' : 'var(--text-subtle)',
            border: 'none',
            cursor: 'pointer',
            fontWeight: 600,
            fontSize: '0.875rem',
          }}
        >
          All Streams
        </button>
        <button
          onClick={() => setActiveTab('air-quality')}
          style={{
            padding: '0.5rem 1.25rem',
            borderRadius: '6px',
            backgroundColor: activeTab === 'air-quality' ? 'var(--primary)' : 'transparent',
            color: activeTab === 'air-quality' ? '#ffffff' : 'var(--text-subtle)',
            border: 'none',
            cursor: 'pointer',
            fontWeight: 600,
            fontSize: '0.875rem',
          }}
        >
          Air Quality Live ({airQualityEvents.length})
        </button>
        <button
          onClick={() => setActiveTab('earthquakes')}
          style={{
            padding: '0.5rem 1.25rem',
            borderRadius: '6px',
            backgroundColor: activeTab === 'earthquakes' ? 'var(--primary)' : 'transparent',
            color: activeTab === 'earthquakes' ? '#ffffff' : 'var(--text-subtle)',
            border: 'none',
            cursor: 'pointer',
            fontWeight: 600,
            fontSize: '0.875rem',
          }}
        >
          Earthquakes Live ({earthquakeEvents.length})
        </button>
      </div>

      {/* Main View Content */}
      {activeTab === 'all' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
          <div>
            <h3 style={{ color: 'var(--primary)', marginBottom: '1rem' }}>Air Quality Live Stream</h3>
            <LiveAirQualityView airQualityData={airQualityEvents} />
          </div>
          <div>
            <h3 style={{ color: '#ef4444', marginBottom: '1rem' }}>Earthquake Live Stream</h3>
            <LiveEarthquakeView earthquakeData={earthquakeEvents} />
          </div>
        </div>
      )}

      {activeTab === 'air-quality' && <LiveAirQualityView airQualityData={airQualityEvents} />}

      {activeTab === 'earthquakes' && <LiveEarthquakeView earthquakeData={earthquakeEvents} />}
    </div>
  );
};

export default LiveMonitoring;
