import React from 'react';
import { CheckCircle2, Clock, AlertCircle, RefreshCw, XCircle } from 'lucide-react';

export const StatusBadge = ({ status }) => {
  if (!status) return null;
  const s = status.toUpperCase();

  let className = 'badge badge-scheduled';
  let Icon = Clock;

  if (s === 'COMPLETED') {
    className = 'badge badge-completed';
    Icon = CheckCircle2;
  } else if (['RUNNING', 'PENDING', 'SCHEDULED'].includes(s)) {
    className = 'badge badge-running';
    Icon = RefreshCw;
  } else if (['FAILED', 'CRASHED', 'CANCELLED'].includes(s)) {
    className = 'badge badge-failed';
    Icon = XCircle;
  }

  return (
    <span className={className}>
      <Icon size={12} className={s === 'RUNNING' ? 'spin-icon' : ''} />
      {s}
      <style>{`
        .spin-icon { animation: spin 1.5s linear infinite; }
      `}</style>
    </span>
  );
};

export default StatusBadge;
