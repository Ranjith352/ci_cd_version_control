import React, { useState } from 'react';
import { Play, RotateCcw } from 'lucide-react';

export const EQForm = ({ onSubmit, isLoading, onReset }) => {
  const [formData, setFormData] = useState({
    start_date: '2026-01-01',
    end_date: '2026-08-20',
    min_magnitude: '2.5',
    max_magnitude: '',
    limit: '1000',
  });

  const [errors, setErrors] = useState({});

  const validate = () => {
    const newErrors = {};

    if (!formData.start_date) {
      newErrors.start_date = 'Start date is required';
    }

    if (!formData.end_date) {
      newErrors.end_date = 'End date is required';
    }

    if (formData.start_date && formData.end_date && formData.start_date > formData.end_date) {
      newErrors.start_date = 'Start date must be less than or equal to end date';
    }

    const minMag = parseFloat(formData.min_magnitude);
    if (isNaN(minMag) || minMag < -1 || minMag > 10) {
      newErrors.min_magnitude = 'Min magnitude must be between -1.0 and 10.0';
    }

    if (formData.max_magnitude !== '') {
      const maxMag = parseFloat(formData.max_magnitude);
      if (isNaN(maxMag) || maxMag < minMag) {
        newErrors.max_magnitude = 'Max magnitude must be >= min magnitude';
      }
    }

    const lim = parseInt(formData.limit, 10);
    if (isNaN(lim) || lim <= 0) {
      newErrors.limit = 'Limit must be a positive integer > 0';
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
        <h3 className="card-title">USGS Earthquake Pipeline Trigger Form</h3>
      </div>

      <form onSubmit={handleSubmit}>
        <div className="form-grid">
          <div className="form-group">
            <label className="form-label" htmlFor="start_date">Start Date</label>
            <input
              type="date"
              id="start_date"
              name="start_date"
              className="form-input"
              value={formData.start_date}
              onChange={handleChange}
            />
            {errors.start_date && <span className="form-error">{errors.start_date}</span>}
          </div>

          <div className="form-group">
            <label className="form-label" htmlFor="end_date">End Date</label>
            <input
              type="date"
              id="end_date"
              name="end_date"
              className="form-input"
              value={formData.end_date}
              onChange={handleChange}
            />
            {errors.end_date && <span className="form-error">{errors.end_date}</span>}
          </div>

          <div className="form-group">
            <label className="form-label" htmlFor="min_magnitude">Minimum Magnitude</label>
            <input
              type="number"
              step="0.1"
              id="min_magnitude"
              name="min_magnitude"
              className="form-input"
              value={formData.min_magnitude}
              onChange={handleChange}
            />
            {errors.min_magnitude && <span className="form-error">{errors.min_magnitude}</span>}
          </div>

          <div className="form-group">
            <label className="form-label" htmlFor="max_magnitude">Maximum Magnitude (Optional)</label>
            <input
              type="number"
              step="0.1"
              id="max_magnitude"
              name="max_magnitude"
              className="form-input"
              value={formData.max_magnitude}
              onChange={handleChange}
              placeholder="e.g. 8.0"
            />
            {errors.max_magnitude && <span className="form-error">{errors.max_magnitude}</span>}
          </div>

          <div className="form-group">
            <label className="form-label" htmlFor="limit">Record Limit</label>
            <input
              type="number"
              id="limit"
              name="limit"
              className="form-input"
              value={formData.limit}
              onChange={handleChange}
            />
            {errors.limit && <span className="form-error">{errors.limit}</span>}
          </div>
        </div>

        <div style={{ display: 'flex', gap: '0.75rem', marginTop: '1rem' }}>
          <button type="submit" className="btn btn-primary" disabled={isLoading}>
            <Play size={16} />
            <span>{isLoading ? 'Triggering Pipeline...' : 'Run USGS Pipeline'}</span>
          </button>

          {onReset && (
            <button type="button" className="btn btn-secondary" onClick={onReset} disabled={isLoading}>
              <RotateCcw size={16} />
              <span>Refresh Data</span>
            </button>
          )}
        </div>
      </form>
    </div>
  );
};

export default EQForm;
