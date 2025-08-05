// React Performance Monitoring Hook
// Tracks component render times and API call performance

import { useEffect, useRef, useState } from 'react';

export const usePerformanceMonitor = (componentName) => {
  const renderStartTime = useRef(Date.now());
  const [renderCount, setRenderCount] = useState(0);

  useEffect(() => {
    const renderTime = Date.now() - renderStartTime.current;
    setRenderCount(prev => prev + 1);
    
    // Log slow renders (> 16ms for 60fps)
    if (renderTime > 16) {
      console.warn(`🐌 Slow render detected: ${componentName} took ${renderTime}ms (render #${renderCount + 1})`);
    }
    
    // Track in performance monitoring
    if (window.performance && window.performance.mark) {
      window.performance.mark(`${componentName}-render-end`);
      if (renderCount === 0) {
        window.performance.mark(`${componentName}-render-start`);
      }
      window.performance.measure(
        `${componentName}-render`,
        `${componentName}-render-start`,
        `${componentName}-render-end`
      );
    }
  });

  useEffect(() => {
    renderStartTime.current = Date.now();
  });

  return { renderCount };
};

export const useAPIPerformance = () => {
  const trackAPICall = (endpoint, startTime) => {
    const duration = Date.now() - startTime;
    
    // Log slow API calls (> 1 second)
    if (duration > 1000) {
      console.warn(`🐌 Slow API call: ${endpoint} took ${duration}ms`);
    }
    
    // Track in performance monitoring
    if (window.performance && window.performance.mark) {
      window.performance.mark(`api-${endpoint}-end`);
      window.performance.measure(
        `api-${endpoint}`,
        `api-${endpoint}-start`,
        `api-${endpoint}-end`
      );
    }
    
    // Send to analytics/monitoring service
    if (window.gtag) {
      window.gtag('event', 'api_performance', {
        custom_parameter_1: endpoint,
        custom_parameter_2: duration,
        value: duration
      });
    }
  };

  const startAPICall = (endpoint) => {
    const startTime = Date.now();
    
    if (window.performance && window.performance.mark) {
      window.performance.mark(`api-${endpoint}-start`);
    }
    
    return { startTime, trackEnd: () => trackAPICall(endpoint, startTime) };
  };

  return { startAPICall };
};

export const useMemoryMonitor = () => {
  const [memoryUsage, setMemoryUsage] = useState(null);

  useEffect(() => {
    const checkMemory = () => {
      if (window.performance && window.performance.memory) {
        const memory = window.performance.memory;
        const memoryInfo = {
          used: Math.round(memory.usedJSHeapSize / 1048576), // MB
          total: Math.round(memory.totalJSHeapSize / 1048576), // MB
          limit: Math.round(memory.jsHeapSizeLimit / 1048576) // MB
        };
        
        setMemoryUsage(memoryInfo);
        
        // Warn if memory usage is high
        const usagePercent = (memoryInfo.used / memoryInfo.limit) * 100;
        if (usagePercent > 80) {
          console.warn(`🚨 High memory usage: ${usagePercent.toFixed(1)}% (${memoryInfo.used}MB/${memoryInfo.limit}MB)`);
        }
      }
    };

    checkMemory();
    const interval = setInterval(checkMemory, 30000); // Check every 30 seconds

    return () => clearInterval(interval);
  }, []);

  return memoryUsage;
};
