/**
 * 🔧 Error Suppression Utility
 * 
 * Suppresses common development errors and provides fallbacks
 */

// Global error handler for development
export const setupDevelopmentErrorHandling = () => {
  // Suppress WebSocket connection errors in development
  const originalConsoleError = console.error;
  
  console.error = (...args) => {
    const message = args.join(' ');
    
    // Filter out common development errors
    const suppressedErrors = [
      'WebSocket connection',
      'Failed to fetch',
      'Network Error',
      'ERR_CONNECTION_REFUSED',
      'websocket connection failed'
    ];
    
    const shouldSuppress = suppressedErrors.some(error => 
      message.toLowerCase().includes(error.toLowerCase())
    );
    
    if (!shouldSuppress) {
      originalConsoleError.apply(console, args);
    } else {
      // Log a simplified message instead
      console.log('🔧 Development: Backend service unavailable, using mock data');
    }
  };

  // Handle unhandled promise rejections
  window.addEventListener('unhandledrejection', (event) => {
    const error = event.reason;
    
    if (error && error.message) {
      const message = error.message.toLowerCase();
      
      if (message.includes('fetch') || 
          message.includes('websocket') || 
          message.includes('network') ||
          message.includes('connection')) {
        
        console.log('🎭 Demo Mode: API service unavailable, continuing with mock data');
        event.preventDefault(); // Prevent error from being thrown
        return;
      }
    }
    
    // For other errors, log them normally
    console.error('Unhandled promise rejection:', error);
  });
};

// Wrapper for API calls that handles errors gracefully
export const safeAPICall = async (apiCall, fallbackData = null) => {
  try {
    return await apiCall();
  } catch (error) {
    console.log('🔧 API call failed, using fallback data');
    return fallbackData;
  }
};

// Initialize error handling
if (import.meta.env.MODE === 'development') {
  setupDevelopmentErrorHandling();
}

export default {
  setupDevelopmentErrorHandling,
  safeAPICall
};
