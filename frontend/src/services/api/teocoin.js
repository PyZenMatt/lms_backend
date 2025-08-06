import api from '../core/axiosClient';

/**
 * Get user's TeoCoin balance from database
 */
export const getTeoCoinBalance = async () => {
  try {
    const response = await api.get('/teocoin/withdrawals/balance/');
    return response.data;
  } catch (error) {
    console.error('Error fetching TeoCoin balance:', error);
    throw error;
  }
};

/**
 * Get TeoCoin discount information for a course
 */
export const getTeoCoinDiscount = async (courseId) => {
  try {
    const response = await api.get(`/courses/${courseId}/teocoin-discount/`);
    return response.data;
  } catch (error) {
    console.error('Error fetching TeoCoin discount:', error);
    throw error;
  }
};

/**
 * Apply TeoCoin discount to course purchase
 */
export const applyTeoCoinDiscount = async (courseId, discountAmount) => {
  try {
    const response = await api.post(`/courses/${courseId}/apply-teocoin-discount/`, {
      discount_amount: discountAmount
    });
    return response.data;
  } catch (error) {
    console.error('Error applying TeoCoin discount:', error);
    throw error;
  }
};
