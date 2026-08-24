import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import LiveMonitoring from '../pages/LiveMonitoring';
import api from '../services/api';

vi.mock('../services/api', () => ({
  default: {
    getLiveAirQuality: vi.fn(),
    getLiveEarthquakes: vi.fn(),
    getLiveHealth: vi.fn(),
    getWebSocketUrl: vi.fn().mockReturnValue('ws://localhost:8000/api/live/ws'),
  },
}));

describe('Live Monitoring Component Suite', () => {
  beforeEach(() => {
    vi.clearAllMocks();

    // Mock global WebSocket for testing
    global.WebSocket = vi.fn().mockImplementation(() => ({
      onopen: null,
      onmessage: null,
      onerror: null,
      onclose: null,
      close: vi.fn(),
      send: vi.fn(),
      readyState: 1,
    }));

    api.getLiveAirQuality.mockResolvedValue({
      source: 'kafka',
      count: 1,
      records: [
        {
          measurement_id: 9991,
          location_name: 'Coimbatore Test Station',
          city: 'Coimbatore',
          country: 'IN',
          parameter: 'pm25',
          value: 18.5,
          unit: 'µg/m³',
          reading_timestamp: '2026-08-24T12:00:00Z',
        },
      ],
    });
    api.getLiveEarthquakes.mockResolvedValue({
      source: 'kafka',
      count: 1,
      events: [
        {
          event_id: 'us7000test',
          magnitude: 4.5,
          place: 'Tokyo, Japan',
          depth_km: 10.0,
          event_time: '2026-08-24T12:00:00Z',
        },
      ],
    });
    api.getLiveHealth.mockResolvedValue({ kafka: 'healthy', redis: 'healthy' });
  });

  it('renders Live Monitoring title and header connection status', async () => {
    render(<LiveMonitoring />);

    expect(screen.getByText('Real-Time Kafka & Redis Monitoring')).toBeInTheDocument();

    await waitFor(() => {
      expect(api.getLiveAirQuality).toHaveBeenCalled();
      expect(api.getLiveEarthquakes).toHaveBeenCalled();
    });
  });

  it('displays tab selectors for Air Quality and Earthquakes', async () => {
    render(<LiveMonitoring />);

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /Air Quality Live/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /Earthquakes Live/i })).toBeInTheDocument();
    });
  });
});
