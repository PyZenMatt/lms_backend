/**
 * API Helper Functions
 * Centralized functions for making API calls with proper error handling
 */

// Get authorization headers
const getAuthHeaders = () => {
  const token = localStorage.getItem('accessToken') || localStorage.getItem('token') || localStorage.getItem('access');
  return {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json',
  };
};

// Base API URL (will be proxied by Vite to /api/v1)
const API_BASE = '/api';

/**
 * Generic API call function
 */
export const apiCall = async (endpoint, options = {}) => {
  const url = `${API_BASE}${endpoint}`;
  const defaultOptions = {
    headers: getAuthHeaders(),
    ...options,
  };

  const response = await fetch(url, defaultOptions);
  
  if (!response.ok) {
    throw new Error(`API call failed: ${response.status} ${response.statusText}`);
  }
  
  return response.json();
};

/**
 * GET request
 */
export const apiGet = async (endpoint) => {
  return apiCall(endpoint, { method: 'GET' });
};

/**
 * POST request
 */
export const apiPost = async (endpoint, data) => {
  return apiCall(endpoint, {
    method: 'POST',
    body: JSON.stringify(data),
  });
};

/**
 * PUT request
 */
export const apiPut = async (endpoint, data) => {
  return apiCall(endpoint, {
    method: 'PUT',
    body: JSON.stringify(data),
  });
};

/**
 * DELETE request
 */
export const apiDelete = async (endpoint) => {
  return apiCall(endpoint, { method: 'DELETE' });
};

/**
 * File upload (FormData)
 */
export const apiUpload = async (endpoint, formData) => {
  const token = localStorage.getItem('accessToken') || localStorage.getItem('token') || localStorage.getItem('access');
  
  return fetch(`${API_BASE}${endpoint}`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      // Don't set Content-Type for FormData, let the browser set it
    },
    body: formData,
  });
};
