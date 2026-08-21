/**
 * Formatting utilities for environmental intelligence dashboard.
 */

export const formatDate = (dateString) => {
  if (!dateString) return 'N/A';
  try {
    const d = new Date(dateString);
    if (isNaN(d.getTime())) return dateString;
    return d.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  } catch {
    return dateString;
  }
};

export const formatDateTime = (dateTimeString) => {
  if (!dateTimeString) return 'N/A';
  try {
    const d = new Date(dateTimeString);
    if (isNaN(d.getTime())) return dateTimeString;
    return d.toLocaleString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  } catch {
    return dateTimeString;
  }
};

export const formatNumber = (val, decimals = 2) => {
  if (val === null || val === undefined || isNaN(val)) return 'N/A';
  return Number(val).toLocaleString('en-US', {
    minimumFractionDigits: 0,
    maximumFractionDigits: decimals,
  });
};

export const getAQIColor = (aqi) => {
  if (aqi === null || aqi === undefined) return '#94a3b8';
  if (aqi <= 50) return '#34d399'; // Good (Green)
  if (aqi <= 100) return '#fbbf24'; // Moderate (Yellow)
  if (aqi <= 150) return '#fb923c'; // Unhealthy for Sensitive Groups (Orange)
  if (aqi <= 200) return '#f87171'; // Unhealthy (Red)
  if (aqi <= 300) return '#c084fc'; // Very Unhealthy (Purple)
  return '#e11d48'; // Hazardous (Maroon)
};

export const getAQICategory = (aqi) => {
  if (aqi === null || aqi === undefined) return 'N/A';
  if (aqi <= 50) return 'Good';
  if (aqi <= 100) return 'Moderate';
  if (aqi <= 150) return 'Unhealthy for Sensitive Groups';
  if (aqi <= 200) return 'Unhealthy';
  if (aqi <= 300) return 'Very Unhealthy';
  return 'Hazardous';
};
