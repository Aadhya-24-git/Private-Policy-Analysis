import { useState, useEffect, useCallback } from 'react';
import { fetchHealthStatus } from '../services/api';

export function useHealth(autoRefreshInterval = 10000) {
  const [healthData, setHealthData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [latencyMs, setLatencyMs] = useState(null);
  const [lastChecked, setLastChecked] = useState(null);

  const checkHealth = useCallback(async () => {
    setLoading(true);
    const result = await fetchHealthStatus();
    setLatencyMs(result.latencyMs);
    setLastChecked(new Date());

    if (result.success) {
      setHealthData(result.data);
      setError(null);
    } else {
      setError(result.error);
    }
    setLoading(false);
  }, []);

  useEffect(() => {
    checkHealth();
    if (autoRefreshInterval > 0) {
      const intervalId = setInterval(checkHealth, autoRefreshInterval);
      return () => clearInterval(intervalId);
    }
  }, [checkHealth, autoRefreshInterval]);

  return {
    healthData,
    loading,
    error,
    latencyMs,
    lastChecked,
    refresh: checkHealth,
  };
}
