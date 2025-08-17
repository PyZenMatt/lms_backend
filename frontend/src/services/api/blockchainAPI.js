/**
 * Blockchain API Service
 * Handles communication with Django backend for TeoCoins operations
 */

import api from '../core/axiosClient';

class BlockchainAPIService {
  /**
   * Get wallet balance from backend
   */
  async getWalletBalance() {
    try {
      const response = await api.get('/blockchain/balance/');
      return response.data;
    } catch (error) {
      console.error('Error fetching wallet balance:', error);
      throw error;
    }
  }

  /**
   * Link wallet address to user account
   */
  async linkWallet(walletAddress) {
    try {
      const response = await api.post('/blockchain/link-wallet/', {
        wallet_address: walletAddress
      });
      return response.data;
    } catch (error) {
      console.error('Error linking wallet:', error);
      throw error;
    }
  }

  /**
   * Send reward to user (admin only)
   */
  async rewardUser(userId, amount, reason = 'Sistema di rewards') {
    try {
      const response = await api.post('/blockchain/reward/', {
        user_id: userId,
        amount: amount,
        reason: reason
      });
      return response.data;
    } catch (error) {
      console.error('Error sending reward:', error);
      throw error;
    }
  }

  /**
   * Get transaction history
   */
  async getTransactionHistory() {
    try {
      const response = await api.get('/blockchain/transactions/');
      return response.data;
    } catch (error) {
      console.error('Error fetching transaction history:', error);
      throw error;
    }
  }

  /**
   * Get token information
   */
  async getTokenInfo() {
    try {
      const response = await api.get('/blockchain/token-info/');
      return response.data;
    } catch (error) {
      console.error('Error fetching token info:', error);
      throw error;
    }
  }

  /**
   * Check transaction status
   */
  async checkTransactionStatus(txHash) {
    try {
      const response = await api.post('/blockchain/check-status/', {
        tx_hash: txHash
      });
      return response.data;
    } catch (error) {
      console.error('Error checking transaction status:', error);
      throw error;
    }
  }

  /**
   * Auto-reward user for course completion
   */
  async autoRewardCourseCompletion(courseId, userId) {
    try {
      const response = await api.post('/blockchain/reward/', {
        user_id: userId,
        amount: '10', // 10 TEO per course completion
        reason: `Completamento corso ID: ${courseId}`
      });
      return response.data;
    } catch (error) {
      console.error('Error in auto-reward:', error);
      throw error;
    }
  }

  /**
   * Auto-reward user for achievement unlock
   */
  async autoRewardAchievement(achievementId, userId, rewardAmount = '5') {
    try {
      const response = await api.post('/blockchain/reward/', {
        user_id: userId,
        amount: rewardAmount,
        reason: `Achievement sbloccato: ${achievementId}`
      });
      return response.data;
    } catch (error) {
      console.error('Error in achievement reward:', error);
      throw error;
    }
  }

  /**
   * Get all platform transactions (admin only)
   */
  async getAdminTransactions(limit = 50, status = null, type = null) {
    try {
      const params = new URLSearchParams();
      params.append('limit', limit);
      if (status) params.append('status', status);
      if (type) params.append('type', type);

      const response = await api.get(`/rewards/admin/transactions/?${params.toString()}`);
      return response.data;
    } catch (error) {
      console.error('Error fetching admin transactions:', error);
      throw error;
    }
  }

  /**
   * Get platform transaction statistics (admin only)
   */
  async getAdminTransactionStats() {
    try {
      const response = await api.get('/rewards/admin/transactions/stats/');
      return response.data;
    } catch (error) {
      console.error('Error fetching admin transaction stats:', error);
      throw error;
    }
  }
}

export const blockchainAPI = new BlockchainAPIService();
export default blockchainAPI;
