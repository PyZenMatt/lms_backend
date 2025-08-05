/**
 * TeoCoin Discount API Service
 * 
 * Provides frontend API calls for the gas-free discount system:
 * - Student discount requests and management
 * - Teacher approval/decline actions
 * - Real-time status tracking
 */

import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';
const DISCOUNT_API_URL = `${API_BASE_URL}/api/v1/services/discount`;

// Configure axios defaults
const api = axios.create({
  baseURL: DISCOUNT_API_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add auth token to requests if available
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

/**
 * Generate signature data for student pre-approval
 */
export const generateSignatureData = async (studentAddress, courseId, coursePrice, discountPercent) => {
  try {
    const response = await api.post('/signature-data/', {
      student_address: studentAddress,
      course_id: courseId,
      course_price: coursePrice,
      discount_percent: discountPercent
    });
    return response.data;
  } catch (error) {
    console.error('Error generating signature data:', error);
    throw new Error(error.response?.data?.error || 'Failed to generate signature data');
  }
};

/**
 * Create a new discount request
 */
export const createDiscountRequest = async (requestData) => {
  try {
    const response = await api.post('/create/', {
      student_address: requestData.studentAddress,
      teacher_address: requestData.teacherAddress,
      course_id: requestData.courseId,
      course_price: requestData.coursePrice,
      discount_percent: requestData.discountPercent,
      student_signature: requestData.studentSignature
    });
    return response.data;
  } catch (error) {
    console.error('Error creating discount request:', error);
    throw new Error(error.response?.data?.error || 'Failed to create discount request');
  }
};

/**
 * Approve a discount request (teacher action)
 */
export const approveDiscountRequest = async (requestId, approverAddress) => {
  try {
    const response = await api.post('/approve/', {
      request_id: requestId,
      approver_address: approverAddress
    });
    return response.data;
  } catch (error) {
    console.error('Error approving discount request:', error);
    throw new Error(error.response?.data?.error || 'Failed to approve discount request');
  }
};

/**
 * Decline a discount request (teacher action)
 */
export const declineDiscountRequest = async (requestId, declinerAddress, reason) => {
  try {
    const response = await api.post('/decline/', {
      request_id: requestId,
      decliner_address: declinerAddress,
      reason: reason
    });
    return response.data;
  } catch (error) {
    console.error('Error declining discount request:', error);
    throw new Error(error.response?.data?.error || 'Failed to decline discount request');
  }
};

/**
 * Get details of a specific discount request
 */
export const getDiscountRequest = async (requestId) => {
  try {
    const response = await api.get(`/request/${requestId}/`);
    return response.data;
  } catch (error) {
    console.error('Error getting discount request:', error);
    throw new Error(error.response?.data?.error || 'Failed to get discount request');
  }
};

/**
 * Get all discount requests for a student
 */
export const getStudentRequests = async (studentAddress) => {
  try {
    const response = await api.get(`/student/${studentAddress}/`);
    return response.data;
  } catch (error) {
    console.error('Error getting student requests:', error);
    throw new Error(error.response?.data?.error || 'Failed to get student requests');
  }
};

/**
 * Get all discount requests for a teacher
 */
export const getTeacherRequests = async (teacherAddress) => {
  try {
    const response = await api.get(`/teacher/${teacherAddress}/`);
    return response.data;
  } catch (error) {
    console.error('Error getting teacher requests:', error);
    throw new Error(error.response?.data?.error || 'Failed to get teacher requests');
  }
};

/**
 * Calculate TEO cost for a given course price and discount percentage
 */
export const calculateDiscountCost = async (coursePrice, discountPercent) => {
  try {
    const response = await api.post('/calculate/', {
      course_price: coursePrice,
      discount_percent: discountPercent
    });
    return response.data;
  } catch (error) {
    console.error('Error calculating discount cost:', error);
    throw new Error(error.response?.data?.error || 'Failed to calculate discount cost');
  }
};

/**
 * Get discount system statistics
 */
export const getDiscountStats = async () => {
  try {
    const response = await api.get('/stats/');
    return response.data;
  } catch (error) {
    console.error('Error getting discount stats:', error);
    throw new Error(error.response?.data?.error || 'Failed to get discount stats');
  }
};

/**
 * Get discount system status and health check
 */
export const getSystemStatus = async () => {
  try {
    const response = await api.get('/status/');
    return response.data;
  } catch (error) {
    console.error('Error getting system status:', error);
    throw new Error(error.response?.data?.error || 'Failed to get system status');
  }
};

/**
 * Helper function to format TEO amounts from wei
 */
export const formatTeoAmount = (amountWei) => {
  return (parseFloat(amountWei) / Math.pow(10, 18)).toFixed(4);
};

/**
 * Helper function to get discount status display name
 */
export const getDiscountStatusName = (status) => {
  const statusNames = {
    0: 'Pending',
    1: 'Approved',
    2: 'Declined', 
    3: 'Expired'
  };
  return statusNames[status] || 'Unknown';
};

export default {
  generateSignatureData,
  createDiscountRequest,
  approveDiscountRequest,
  declineDiscountRequest,
  getDiscountRequest,
  getStudentRequests,
  getTeacherRequests,
  calculateDiscountCost,
  getDiscountStats,
  getSystemStatus,
  formatTeoAmount,
  getDiscountStatusName
};
