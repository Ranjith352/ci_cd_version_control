import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import App from '../App';
import api from '../services/api';

vi.mock('../services/api', () => ({
  default: {
    getHealth: vi.fn(),
    getTrends: vi.fn(),
    getAirQualityVisualization: vi.fn(),
    getEarthquakeVisualization: vi.fn(),
    triggerOpenAQ: vi.fn(),
    triggerUSGS: vi.fn(),
    getFlowStatus: vi.fn(),
  },
}));

describe('Environmental Intelligence Frontend Suite', () => {
  beforeEach(() => {
    vi.clearAllMocks();

    api.getHealth.mockResolvedValue({ status: 'healthy', service: 'environmental-intelligence-api' });
    api.getTrends.mockResolvedValue({ total_days: 1, trends: [{ date: '2026-08-20', pm25_avg: 22.4, earthquake_count: 5 }] });
    api.getAirQualityVisualization.mockResolvedValue({
      city: 'Coimbatore',
      parameter: 'pm25',
      total_records: 1,
      data: [{ date: '2026-08-20', avg_concentration: 22.4, max_aqi: 72 }],
    });
    api.getEarthquakeVisualization.mockResolvedValue({
      total_events: 1,
      min_magnitude: 2.5,
      max_magnitude: 5.4,
      events: [{ event_id: 'us7000m123', event_time: '2026-08-20T08:14:22Z', magnitude: 5.4, magnitude_category: 'Moderate', latitude: 42.28, longitude: 143.42, depth_km: 35.2, tsunami: 0 }],
      regional_summary: [{ region: 'Japan', total_events: 1, max_magnitude: 5.4, avg_depth_km: 35.2, tsunami_alerts: 0 }],
      monthly_categories: [{ month: '2026-08', magnitude_category: 'Moderate', event_count: 1 }],
    });
  });

  it('renders Dashboard page title and navigation links', async () => {
    render(<App />);
    expect(screen.getAllByText('Environmental Intelligence')[0]).toBeInTheDocument();
    await waitFor(() => {
      expect(screen.getByText('Executive Overview')).toBeInTheDocument();
    });
  });

  it('renders Air Quality form and validates required fields', async () => {
    render(<App />);
    const aqNavs = screen.getAllByText('Air Quality');
    fireEvent.click(aqNavs[0]);

    await waitFor(() => {
      expect(screen.getAllByText('Air Quality Intelligence')[0]).toBeInTheDocument();
    });

    const cityInput = screen.getByLabelText('City Name');
    fireEvent.change(cityInput, { target: { value: '' } });

    const submitBtn = screen.getByText('Run OpenAQ Pipeline');
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(screen.getByText('City name is required')).toBeInTheDocument();
    });
  });

  it('renders Earthquake form and validates date order', async () => {
    render(<App />);
    const eqNavs = screen.getAllByText('Earthquakes');
    fireEvent.click(eqNavs[0]);

    await waitFor(() => {
      expect(screen.getAllByText('Earthquake Hazard Intelligence')[0]).toBeInTheDocument();
    });

    const startDateInput = screen.getByLabelText('Start Date');
    const endDateInput = screen.getByLabelText('End Date');

    fireEvent.change(startDateInput, { target: { value: '2026-08-20' } });
    fireEvent.change(endDateInput, { target: { value: '2026-01-01' } });

    const submitBtn = screen.getByText('Run USGS Pipeline');
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(screen.getByText('Start date must be less than or equal to end date')).toBeInTheDocument();
    });
  });

  it('triggers OpenAQ pipeline and displays returned flow_run_id', async () => {
    api.triggerOpenAQ.mockResolvedValue({ status: 'triggered', pipeline: 'openaq', flow_run_id: 'flow_run_openaq_12345' });
    api.getFlowStatus.mockResolvedValue({ flow_run_id: 'flow_run_openaq_12345', status: 'COMPLETED', state_type: 'COMPLETED', message: 'Success' });

    render(<App />);
    const aqNavs = screen.getAllByText('Air Quality');
    fireEvent.click(aqNavs[0]);

    await waitFor(() => {
      expect(screen.getAllByText('Air Quality Intelligence')[0]).toBeInTheDocument();
    });

    const submitBtn = screen.getByText('Run OpenAQ Pipeline');
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(api.triggerOpenAQ).toHaveBeenCalled();
      expect(screen.getByText('flow_run_openaq_12345')).toBeInTheDocument();
    });
  });
});
