import { useState, useEffect, useRef, useCallback } from 'react';
import api from '../services/api';

/**
 * Custom hook for polling Prefect flow status.
 */
export const useFlowStatus = (flowRunId, options = {}) => {
  const {
    onCompleted,
    onFailed,
    intervalMs = 3000,
    maxPolls = 60,
  } = options;

  const [status, setStatus] = useState(null);
  const [stateType, setStateType] = useState(null);
  const [message, setMessage] = useState('');
  const [isPolling, setIsPolling] = useState(false);
  const [error, setError] = useState(null);

  const pollCountRef = useRef(0);
  const timerRef = useRef(null);

  const stopPolling = useCallback(() => {
    if (timerRef.current) {
      clearTimeout(timerRef.current);
      timerRef.current = null;
    }
    setIsPolling(false);
  }, []);

  useEffect(() => {
    if (!flowRunId) {
      stopPolling();
      setStatus(null);
      setStateType(null);
      setMessage('');
      setError(null);
      return;
    }

    pollCountRef.current = 0;
    setIsPolling(true);
    setError(null);

    const checkStatus = async () => {
      try {
        pollCountRef.current += 1;
        if (pollCountRef.current > maxPolls) {
          stopPolling();
          const err = 'Flow status polling timed out after maximum attempts.';
          setError(err);
          if (onFailed) onFailed(err);
          return;
        }

        const res = await api.getFlowStatus(flowRunId);
        setStatus(res.status);
        setStateType(res.state_type);
        setMessage(res.message || '');

        const currentStatus = (res.status || '').toUpperCase();

        if (currentStatus === 'COMPLETED') {
          stopPolling();
          if (onCompleted) onCompleted(res);
        } else if (['FAILED', 'CRASHED', 'CANCELLED'].includes(currentStatus)) {
          stopPolling();
          const errMsg = res.message || `Flow run ended with status ${currentStatus}`;
          setError(errMsg);
          if (onFailed) onFailed(errMsg);
        } else {
          // Schedule next poll
          timerRef.current = setTimeout(checkStatus, intervalMs);
        }
      } catch (err) {
        stopPolling();
        const errMsg = err.message || 'Failed to poll flow status.';
        setError(errMsg);
        if (onFailed) onFailed(errMsg);
      }
    };

    checkStatus();

    return () => {
      stopPolling();
    };
  }, [flowRunId, intervalMs, maxPolls, stopPolling]);

  return {
    status,
    stateType,
    message,
    isPolling,
    error,
    stopPolling,
  };
};

export default useFlowStatus;
