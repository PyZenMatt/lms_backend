/**
 * 🔧 Development Configuration
 * 
 * Handles fallback to mock services when backend is not available
 */

// Check if we're in development mode
export const isDevelopment = import.meta.env.MODE === 'development';

// API endpoints availability
export const checkAPIAvailability = async () => {
  const endpoints = {
    activity: false,
    websocket: false,
    staking: false,
    teacher: false
  };

  try {
    // Quick health check for each service
    const checks = await Promise.allSettled([
      fetch('/api/v1/activity/feed/', { method: 'HEAD' }),
      fetch('/api/v1/teocoin/staking-info/', { method: 'HEAD' }),
      fetch('/api/v1/teacher/profile/', { method: 'HEAD' })
    ]);

    endpoints.activity = checks[0].status === 'fulfilled' && checks[0].value.ok;
    endpoints.staking = checks[1].status === 'fulfilled' && checks[1].value.ok;
    endpoints.teacher = checks[2].status === 'fulfilled' && checks[2].value.ok;

    // WebSocket check
    try {
      const ws = new WebSocket(`ws://localhost:8000/ws/test/`);
      ws.onopen = () => {
        endpoints.websocket = true;
        ws.close();
      };
      ws.onerror = () => {
        endpoints.websocket = false;
      };
    } catch {
      endpoints.websocket = false;
    }

  } catch (error) {
    console.log('🔧 Backend services not available, using mock data');
  }

  return endpoints;
};

// Global flag for mock mode
let mockMode = false;

export const setMockMode = (enabled) => {
  mockMode = enabled;
  if (enabled) {
    console.log('🎭 Demo Mode: Using mock data for all services');
  }
};

export const isMockMode = () => mockMode;

// Initialize mock mode detection
export const initializeDevelopmentMode = async () => {
  if (isDevelopment) {
    const availability = await checkAPIAvailability();
    const allServicesDown = !Object.values(availability).some(Boolean);
    
    if (allServicesDown) {
      setMockMode(true);
      return true;
    }
  }
  return false;
};

export default {
  isDevelopment,
  checkAPIAvailability,
  setMockMode,
  isMockMode,
  initializeDevelopmentMode
};
