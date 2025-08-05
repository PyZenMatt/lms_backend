import api from '../core/axiosClient';

/**
 * Fetches information about the reward pool, including balances and status
 * 
 * @returns {Promise} Promise that resolves with reward pool data
 */
export const getRewardPoolInfo = async () => {
  return api.get('blockchain/reward-pool-info/');
};

/**
 * Refills the reward pool with MATIC from the admin wallet
 * 
 * @param {string} amount - Amount of MATIC to transfer
 * @returns {Promise} Promise that resolves with transaction data
 */
export const refillRewardPool = async (amount) => {
  return api.post('blockchain/refill-reward-pool/', { amount });
};

/**
 * Fetches blockchain transaction history with pagination and filters
 * 
 * @param {Object} params - Query parameters
 * @param {number} params.page - Page number
 * @param {number} params.pageSize - Number of transactions per page
 * @param {string} params.transactionType - Filter by transaction type
 * @param {string} params.startDate - Filter by start date
 * @param {string} params.endDate - Filter by end date
 * @returns {Promise} Promise that resolves with transaction history
 */
export const getBlockchainTransactions = async (params = {}) => {
  return api.get('blockchain/transactions/', { params });
};

/**
 * Manually transfer TeoCoins to a user
 * 
 * @param {Object} transferData - Transfer data
 * @param {string} transferData.toAddress - Recipient wallet address
 * @param {string} transferData.amount - Amount of TeoCoins to transfer
 * @returns {Promise} Promise that resolves with transaction data
 */
export const manualTeoCoinTransfer = async (transferData) => {
  return api.post('blockchain/reward/', transferData);
};
