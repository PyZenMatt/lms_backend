/**
 * Gas-Free V2 API Client
 * Dedicated client for zero-MATIC gas-free endpoints
 */

import axios from 'axios';

// Create V2 API instance for gas-free endpoints
const apiV2 = axios.create({
  baseURL: import.meta.env.VITE_REACT_APP_BACKEND_URL || 'http://localhost:8000/api/v2',
  timeout: 15000, // Longer timeout for blockchain operations
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor - Add authentication token
apiV2.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('accessToken') || 
                  localStorage.getItem('token') || 
                  localStorage.getItem('access');
    
    if (token) {
      config.headers['Authorization'] = `Bearer ${token}`;
    }
    
    // Don't override Content-Type for FormData
    if (config.data instanceof FormData) {
      delete config.headers['Content-Type'];
    }
    
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor - Handle common errors
apiV2.interceptors.response.use(
  (response) => response,
  (error) => {
    // Handle token expiration
    if (error.response?.status === 401) {
      const tokenError = error.response.data?.code === 'token_not_valid' ||
                        error.response.data?.detail?.includes('token');
      
      if (tokenError) {
        // Clear tokens and redirect to login
        localStorage.removeItem('accessToken');
        localStorage.removeItem('refreshToken');
        localStorage.removeItem('token');
        localStorage.removeItem('access');
        
        // Only redirect if not already on login page
        if (!window.location.pathname.includes('/login')) {
          window.location.href = '/login';
        }
      }
    }
    
    // Log errors in development
    if (import.meta.env.DEV) {
      console.error('Gas-Free API V2 Error:', {
        url: error.config?.url,
        method: error.config?.method,
        status: error.response?.status,
        data: error.response?.data,
      });
    }
    
    return Promise.reject(error);
  }
);

// Error handler utility for V2 APIs
export const handleV2ApiError = (error, fallbackMessage = 'Gas-free operation failed') => {
  if (error.response?.data?.error) {
    return error.response.data.error;
  }
  
  if (error.response?.data?.detail) {
    return error.response.data.detail;
  }
  
  if (error.response?.data?.message) {
    return error.response.data.message;
  }
  
  if (error.message) {
    return error.message;
  }
  
  return fallbackMessage;
};

export default apiV2;
