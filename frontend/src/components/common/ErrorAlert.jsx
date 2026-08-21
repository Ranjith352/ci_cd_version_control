import React from 'react';
import { AlertTriangle } from 'lucide-react';

export const ErrorAlert = ({ title = 'Error', message, onRetry }) => {
  if (!message) return null;
  return (
    <div style={{
      backgroundColor: 'var(--danger-bg)',
      border: '1px solid rgba(248, 113, 113, 0.3)',
      borderRadius: '0.5rem',
      padding: '1rem 1.25rem',
      marginBottom: '1.25rem',
      display: 'flex',
      alignItems: 'flex-start',
      gap: '0.75rem',
      color: 'var(--danger)',
    }}>
      <AlertTriangle size={20} style={{ flexShrink: 0, marginTop: '2px' }} />
      <div style={{ flex: 1 }}>
        <div style={{ fontWeight: 600, fontSize: '0.9375rem', marginBottom: '0.25rem' }}>{title}</div>
        <div style={{ fontSize: '0.875rem', color: '#fca5a5' }}>{message}</div>
        {onRetry && (
          <button
            onClick={onRetry}
            style={{
              marginTop: '0.5rem',
              backgroundColor: 'rgba(248, 113, 113, 0.2)',
              border: 'none',
              borderRadius: '0.25rem',
              padding: '0.25rem 0.625rem',
              color: '#ffffff',
              fontSize: '0.75rem',
              fontWeight: 600,
              cursor: 'pointer',
            }}
          >
            Retry Connection
          </button>
        )}
      </div>
    </div>
  );
};

export default ErrorAlert;
