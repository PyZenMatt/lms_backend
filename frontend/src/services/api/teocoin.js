/**
 * TeoCoin API Service
 * 
 * Provides frontend API calls for TeoCoin wallet operations:
 * - Balance management
 * - Staking functionality 
 * - Burn deposits
 * - Transaction history
 */

import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

// Configure axios defaults
const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 15000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add auth token to requests if available
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('accessToken');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

/**
 * Get user's TeoCoin balance and wallet info
 */
export const getWalletBalance = async () => {
  try {
    const response = await api.get('/api/v1/teocoin/balance/');
    return response.data;
  } catch (error) {
    console.error('Error getting wallet balance:', error);
    throw new Error(error.response?.data?.error || 'Failed to get wallet balance');
  }
};

/**
 * Get staking information and tiers
 */
export const getStakingInfo = async () => {
  try {
    const response = await api.get('/api/v1/teocoin/staking/info/');
    return response.data;
  } catch (error) {
    console.error('Error getting staking info:', error);
    throw new Error(error.response?.data?.error || 'Failed to get staking info');
  }
};

/**
 * Stake TeoCoin tokens
 */
export const stakeTokens = async (amount, tier = 'basic') => {
  try {
    const response = await api.post('/api/v1/teocoin/staking/stake/', {
      amount: amount,
      tier: tier
    });
    return response.data;
  } catch (error) {
    console.error('Error staking tokens:', error);
    throw new Error(error.response?.data?.error || 'Failed to stake tokens');
  }
};

/**
 * Unstake TeoCoin tokens
 */
export const unstakeTokens = async (stakingId) => {
  try {
    const response = await api.post('/api/v1/teocoin/staking/unstake/', {
      staking_id: stakingId
    });
    return response.data;
  } catch (error) {
    console.error('Error unstaking tokens:', error);
    throw new Error(error.response?.data?.error || 'Failed to unstake tokens');
  }
};

/**
 * Get user's staking positions
 */
export const getStakingPositions = async () => {
  try {
    const response = await api.get('/api/v1/teocoin/staking/positions/');
    return response.data;
  } catch (error) {
    console.error('Error getting staking positions:', error);
    throw new Error(error.response?.data?.error || 'Failed to get staking positions');
  }
};

/**
 * Process burn deposit (convert blockchain tokens to platform balance)
 */
export const burnDeposit = async (transactionHash, amount, metamaskAddress) => {
  try {
    const response = await api.post('/api/v1/teocoin/burn-deposit/', {
      transaction_hash: transactionHash,
      amount: amount,
      metamask_address: metamaskAddress
    });
    return response.data;
  } catch (error) {
    console.error('Error processing burn deposit:', error);
    throw new Error(error.response?.data?.error || 'Failed to process burn deposit');
  }
};

/**
 * Get burn deposit history
 */
export const getBurnHistory = async () => {
  try {
    const response = await api.get('/api/v1/teocoin/burn-deposit/history/');
    return response.data;
  } catch (error) {
    console.error('Error getting burn history:', error);
    throw new Error(error.response?.data?.error || 'Failed to get burn history');
  }
};

/**
 * Get transaction history
 */
export const getTransactionHistory = async (limit = 50, offset = 0) => {
  try {
    const response = await api.get(`/api/v1/teocoin/transactions/?limit=${limit}&offset=${offset}`);
    return response.data;
  } catch (error) {
    console.error('Error getting transaction history:', error);
    throw new Error(error.response?.data?.error || 'Failed to get transaction history');
  }
};

/**
 * Get withdrawal requests
 */
export const getWithdrawals = async () => {
  try {
    const response = await api.get('/api/v1/teocoin/withdrawals/');
    return response.data;
  } catch (error) {
    console.error('Error getting withdrawals:', error);
    throw new Error(error.response?.data?.error || 'Failed to get withdrawals');
  }
};

/**
 * Create withdrawal request
 */
export const createWithdrawal = async (amount, walletAddress) => {
  try {
    const response = await api.post('/api/v1/teocoin/withdrawals/create/', {
      amount: amount,
      wallet_address: walletAddress
    });
    return response.data;
  } catch (error) {
    console.error('Error creating withdrawal:', error);
    throw new Error(error.response?.data?.error || 'Failed to create withdrawal');
  }
};

/**
 * Helper function to format TeoCoin amounts
 */
export const formatTeoAmount = (amount, decimals = 2) => {
  return new Intl.NumberFormat('en-US', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals
  }).format(parseFloat(amount) || 0);
};

/**
 * Helper function to get staking tier info
 */
export const getStakingTierInfo = (tier) => {
  const tiers = {
    basic: {
      name: 'Basic',
      minAmount: 100,
      apy: 8,
      lockPeriod: 30,
      color: 'primary'
    },
    premium: {
      name: 'Premium', 
      minAmount: 500,
      apy: 12,
      lockPeriod: 90,
      color: 'warning'
    },
    pro: {
      name: 'Professional',
      minAmount: 1000,
      apy: 15,
      lockPeriod: 180,
      color: 'success'
    }
  };
  return tiers[tier] || tiers.basic;
};

export default {
  getWalletBalance,
  getStakingInfo,
  stakeTokens,
  unstakeTokens,
  getStakingPositions,
  burnDeposit,
  getBurnHistory,
  getTransactionHistory,
  getWithdrawals,
  createWithdrawal,
  formatTeoAmount,
  getStakingTierInfo
};
