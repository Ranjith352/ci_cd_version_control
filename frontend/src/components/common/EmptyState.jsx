import React from 'react';
import { Database } from 'lucide-react';

export const EmptyState = ({ title = 'No Data Available', message = 'No visualization records matched your selected filters.' }) => {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '3rem 1rem', textAlign: 'center', color: 'var(--text-subtle)' }}>
      <Database size={40} style={{ marginBottom: '0.75rem', opacity: 0.5 }} />
      <h4 style={{ color: 'var(--text-muted)', fontSize: '1rem', fontWeight: 600, marginBottom: '0.25rem' }}>{title}</h4>
      <p style={{ fontSize: '0.875rem', maxWidth: '360px' }}>{message}</p>
    </div>
  );
};

export default EmptyState;
