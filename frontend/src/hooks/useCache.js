import React, { useState, useEffect, useCallback } from 'react';

// Hook for managing local storage with caching
const useLocalStorage = (key, initialValue) => {
  const [storedValue, setStoredValue] = useState(() => {
    try {
      const item = window.localStorage.getItem(key);
      return item ? JSON.parse(item) : initialValue;
    } catch (error) {
      console.error(`Error reading localStorage key "${key}":`, error);
      return initialValue;
    }
  });

  const setValue = useCallback((value) => {
    try {
      const valueToStore = value instanceof Function ? value(storedValue) : value;
      setStoredValue(valueToStore);
      window.localStorage.setItem(key, JSON.stringify(valueToStore));
    } catch (error) {
      console.error(`Error setting localStorage key "${key}":`, error);
    }
  }, [key, storedValue]);

  const removeValue = useCallback(() => {
    try {
      window.localStorage.removeItem(key);
      setStoredValue(initialValue);
    } catch (error) {
      console.error(`Error removing localStorage key "${key}":`, error);
    }
  }, [key, initialValue]);

  return [storedValue, setValue, removeValue];
};

// Hook for managing session storage
const useSessionStorage = (key, initialValue) => {
  const [storedValue, setStoredValue] = useState(() => {
    try {
      const item = window.sessionStorage.getItem(key);
      return item ? JSON.parse(item) : initialValue;
    } catch (error) {
      console.error(`Error reading sessionStorage key "${key}":`, error);
      return initialValue;
    }
  });

  const setValue = useCallback((value) => {
    try {
      const valueToStore = value instanceof Function ? value(storedValue) : value;
      setStoredValue(valueToStore);
      window.sessionStorage.setItem(key, JSON.stringify(valueToStore));
    } catch (error) {
      console.error(`Error setting sessionStorage key "${key}":`, error);
    }
  }, [key, storedValue]);

  const removeValue = useCallback(() => {
    try {
      window.sessionStorage.removeItem(key);
      setStoredValue(initialValue);
    } catch (error) {
      console.error(`Error removing sessionStorage key "${key}":`, error);
    }
  }, [key, initialValue]);

  return [storedValue, setValue, removeValue];
};

// Hook for memory cache with TTL (time to live)
const useMemoryCache = (ttl = 5 * 60 * 1000) => { // default 5 minutes
  const [cache, setCache] = useState(new Map());

  const set = useCallback((key, value) => {
    const expiresAt = Date.now() + ttl;
    setCache(prev => new Map(prev).set(key, { value, expiresAt }));
  }, [ttl]);

  const get = useCallback((key) => {
    const cached = cache.get(key);
    if (!cached) return null;
    
    if (Date.now() > cached.expiresAt) {
      setCache(prev => {
        const newCache = new Map(prev);
        newCache.delete(key);
        return newCache;
      });
      return null;
    }
    
    return cached.value;
  }, [cache]);

  const remove = useCallback((key) => {
    setCache(prev => {
      const newCache = new Map(prev);
      newCache.delete(key);
      return newCache;
    });
  }, []);

  const clear = useCallback(() => {
    setCache(new Map());
  }, []);

  const has = useCallback((key) => {
    const cached = cache.get(key);
    if (!cached) return false;
    
    if (Date.now() > cached.expiresAt) {
      remove(key);
      return false;
    }
    
    return true;
  }, [cache, remove]);

  // Clean up expired entries periodically
  useEffect(() => {
    const interval = setInterval(() => {
      const now = Date.now();
      setCache(prev => {
        const newCache = new Map();
        for (const [key, item] of prev) {
          if (now <= item.expiresAt) {
            newCache.set(key, item);
          }
        }
        return newCache;
      });
    }, 60000); // Check every minute

    return () => clearInterval(interval);
  }, []);

  return { set, get, remove, clear, has };
};

export { useLocalStorage, useSessionStorage, useMemoryCache };
