import { useState, useCallback, useRef } from 'react';

/**
 * Custom hook for batching multiple API calls
 * Reduces network requests and improves performance
 */
export const useBatchApi = (batchSize = 5, delay = 100) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const batchQueue = useRef([]);
  const timeoutRef = useRef(null);

  const executeBatch = useCallback(async () => {
    if (batchQueue.current.length === 0) return;

    setLoading(true);
    setError(null);

    try {
      const requests = [...batchQueue.current];
      batchQueue.current = [];

      // Execute all requests in parallel
      const results = await Promise.allSettled(
        requests.map(({ request }) => request())
      );

      // Process results
      results.forEach((result, index) => {
        const { resolve, reject } = requests[index];
        if (result.status === 'fulfilled') {
          resolve(result.value);
        } else {
          reject(result.reason);
        }
      });
    } catch (err) {
      setError(err);
      // Reject all pending requests
      batchQueue.current.forEach(({ reject }) => reject(err));
      batchQueue.current = [];
    } finally {
      setLoading(false);
    }
  }, []);

  const addToBatch = useCallback((request) => {
    return new Promise((resolve, reject) => {
      batchQueue.current.push({ request, resolve, reject });

      // Clear existing timeout
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }

      // Execute batch when it reaches batchSize or after delay
      if (batchQueue.current.length >= batchSize) {
        executeBatch();
      } else {
        timeoutRef.current = setTimeout(executeBatch, delay);
      }
    });
  }, [batchSize, delay, executeBatch]);

  const flushBatch = useCallback(() => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }
    executeBatch();
  }, [executeBatch]);

  return {
    addToBatch,
    flushBatch,
    loading,
    error
  };
};
