import React, { useState } from 'react';
import { Play, RotateCcw } from 'lucide-react';

export const AQForm = ({ onSubmit, isLoading, onReset }) => {
  const [formData, setFormData] = useState({
    city: 'Coimbatore',
    latitude: '11.0168',
    longitude: '76.9558',
    radius: '25000',
    measurement_limit: '2000',
  });

  const [errors, setErrors] = useState({});

  const validate = () => {
    const newErrors = {};

    if (!formData.city || !formData.city.trim()) {
      newErrors.city = 'City name is required';
    }

    const lat = parseFloat(formData.latitude);
    if (isNaN(lat) || lat < -90 || lat > 90) {
      newErrors.latitude = 'Latitude must be a valid number between -90 and 90';
    }

    const lon = parseFloat(formData.longitude);
    if (isNaN(lon) || lon < -180 || lon > 180) {
      newErrors.longitude = 'Longitude must be a valid number between -180 and 180';
    }

    const rad = parseInt(formData.radius, 10);
    if (isNaN(rad) || rad <= 0) {
      newErrors.radius = 'Radius must be a positive integer > 0';
    }

    const limit = parseInt(formData.measurement_limit, 10);
    if (isNaN(limit) || limit <= 0) {
      newErrors.measurement_limit = 'Measurement limit must be a positive integer > 0';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
    if (errors[name]) {
      setErrors((prev) => ({ ...prev, [name]: undefined }));
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (validate()) {
      onSubmit(formData);
    }
  };

  return (
    <div className="card">
      <div className="card-header">
        <h3 className="card-title">OpenAQ Pipeline Trigger Form</h3>
      </div>

      <form onSubmit={handleSubmit}>
        <div className="form-grid">
          <div className="form-group">
            <label className="form-label" htmlFor="city">City Name</label>
            <input
              type="text"
              id="city"
              name="city"
              className="form-input"
              value={formData.city}
              onChange={handleChange}
              placeholder="e.g. Coimbatore"
            />
            {errors.city && <span className="form-error">{errors.city}</span>}
          </div>

          <div className="form-group">
            <label className="form-label" htmlFor="latitude">Latitude</label>
            <input
              type="number"
              step="any"
              id="latitude"
              name="latitude"
              className="form-input"
              value={formData.latitude}
              onChange={handleChange}
            />
            {errors.latitude && <span className="form-error">{errors.latitude}</span>}
          </div>

          <div className="form-group">
            <label className="form-label" htmlFor="longitude">Longitude</label>
            <input
              type="number"
              step="any"
              id="longitude"
              name="longitude"
              className="form-input"
              value={formData.longitude}
              onChange={handleChange}
            />
            {errors.longitude && <span className="form-error">{errors.longitude}</span>}
          </div>

          <div className="form-group">
            <label className="form-label" htmlFor="radius">Search Radius (meters)</label>
            <input
              type="number"
              id="radius"
              name="radius"
              className="form-input"
              value={formData.radius}
              onChange={handleChange}
            />
            {errors.radius && <span className="form-error">{errors.radius}</span>}
          </div>

          <div className="form-group">
            <label className="form-label" htmlFor="measurement_limit">Measurement Limit</label>
            <input
              type="number"
              id="measurement_limit"
              name="measurement_limit"
              className="form-input"
              value={formData.measurement_limit}
              onChange={handleChange}
            />
            {errors.measurement_limit && <span className="form-error">{errors.measurement_limit}</span>}
          </div>
        </div>

        <div style={{ display: 'flex', gap: '0.75rem', marginTop: '1rem' }}>
          <button type="submit" className="btn btn-primary" disabled={isLoading}>
            <Play size={16} />
            <span>{isLoading ? 'Triggering Pipeline...' : 'Run OpenAQ Pipeline'}</span>
          </button>

          {onReset && (
            <button type="button" className="btn btn-secondary" onClick={onReset} disabled={isLoading}>
              <RotateCcw size={16} />
              <span>Refresh Visualization</span>
            </button>
          )}
        </div>
      </form>
    </div>
  );
};

export default AQForm;
