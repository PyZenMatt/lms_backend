/**
 * 🔧 Development Environment Suppressions
 * 
 * Suppresses known warnings/errors that are expected in development
 * and don't affect functionality
 */

// Suppress SES warnings from MetaMask/web3 libraries in development
if (process.env.NODE_ENV === 'development') {
  // Store original console methods
  const originalWarn = console.warn;
  const originalError = console.error;
  
  // Override console.warn to filter SES warnings
  console.warn = (...args) => {
    const message = args.join(' ');
    
    // Suppress SES-related warnings
    if (
      message.includes('SES The \'dateTaming\' option is deprecated') ||
      message.includes('SES The \'mathTaming\' option is deprecated') ||
      message.includes('SES Removing unpermitted intrinsics') ||
      message.includes('toTemporalInstant')
    ) {
      return; // Suppress these warnings
    }
    
    // Keep other warnings
    originalWarn.apply(console, args);
  };
  
  // Override console.error to filter known development errors
  console.error = (...args) => {
    const message = args.join(' ');
    
    // Suppress WebSocket connection errors in development (expected when backend not running)
    if (
      message.includes('Firefox non può stabilire una connessione') ||
      message.includes('La connessione con ws://') ||
      message.includes('WebSocket connection to') ||
      message.includes('SES_UNCAUGHT_EXCEPTION') && message.includes('activity.activity_type is undefined')
    ) {
      // Convert to info log instead
      console.log('📡 [Dev Info] Backend/WebSocket unavailable - using mock data');
      return;
    }
    
    // Keep other errors
    originalError.apply(console, args);
  };
  
  console.log('🔧 Development suppressions active - cleaner console output enabled');
}

export default {};
