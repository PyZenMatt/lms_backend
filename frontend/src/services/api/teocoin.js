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

// NOTE: The applyTeoCoinDiscount function has been removed.
// TeoCoin discount is now automatically applied during payment confirmation
// in the CreatePaymentIntentView → ConfirmPaymentView flow.
// No separate API call is needed to apply the discount.
