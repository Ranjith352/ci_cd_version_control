import axios from 'axios';

const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

const apiClient = axios.create({
  baseURL: BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000,
});

// Response interceptor for unified error parsing
apiClient.interceptors.response.use(
  (response) => response.data,
  (error) => {
    let message = 'An unexpected error occurred';
    if (error.response) {
      const data = error.response.data;
      message = data?.detail || data?.message || `HTTP ${error.response.status} Error`;
    } else if (error.request) {
      message = 'Unable to connect to backend server. Please verify FastAPI is running.';
    } else {
      message = error.message;
    }
    return Promise.reject(new Error(message));
  }
);

export const api = {
  getHealth: () => apiClient.get('/health'),

  triggerPipeline: (payload) => apiClient.post('/api/trigger', payload),

  triggerOpenAQ: (params) =>
    apiClient.post('/api/trigger', {
      pipeline: 'openaq',
      city: params.city || 'Coimbatore',
      latitude: parseFloat(params.latitude ?? 11.0168),
      longitude: parseFloat(params.longitude ?? 76.9558),
      radius: parseInt(params.radius ?? 25000, 10),
      measurement_limit: parseInt(params.measurement_limit ?? 2000, 10),
    }),

  triggerUSGS: (params) =>
    apiClient.post('/api/trigger', {
      pipeline: 'usgs',
      start_date: params.start_date || '2026-01-01',
      end_date: params.end_date || '2026-08-20',
      min_magnitude: parseFloat(params.min_magnitude ?? 2.5),
      max_magnitude: params.max_magnitude ? parseFloat(params.max_magnitude) : null,
      limit: parseInt(params.limit ?? 1000, 10),
    }),

  getFlowStatus: (runId) => apiClient.get(`/api/status/${runId}`),

  getAirQualityVisualization: (params = {}) =>
    apiClient.get('/api/visualization/air-quality', { params }),

  getEarthquakeVisualization: (params = {}) =>
    apiClient.get('/api/visualization/earthquakes', { params }),

  getTrends: (params = {}) => apiClient.get('/api/analytics/trends', { params }),
};

export default api;
