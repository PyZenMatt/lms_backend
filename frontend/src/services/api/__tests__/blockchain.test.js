/**
 * Blockchain Service Tests
 * Testing /services/api/blockchain.js functionality
 */

import {
  getRewardPoolInfo,
  refillRewardPool,
  getBlockchainTransactions,
  manualTeoCoinTransfer
} from '../blockchain';
import api from '../../core/axiosClient';

// Mock the apiClient
jest.mock('../../core/apiClient', () => ({
  __esModule: true,
  default: {
    get: jest.fn(),
    post: jest.fn(),
    put: jest.fn(),
    delete: jest.fn(),
  },
}));

describe('Blockchain Service', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('getRewardPoolInfo', () => {
    it('should fetch reward pool information', async () => {
      const mockResponse = {
        data: {
          pool_balance: '1000.0',
          total_distributed: '500.0',
          pool_status: 'active',
          admin_wallet: '0xadmin123...',
          last_refill_date: '2025-06-20T10:00:00Z',
          transactions_count: 150
        }
      };

      api.get.mockResolvedValue(mockResponse);

      const result = await getRewardPoolInfo();

      expect(api.get).toHaveBeenCalledWith('blockchain/reward-pool-info/');
      expect(result).toEqual(mockResponse);
    });

    it('should handle reward pool info fetch errors', async () => {
      const mockError = {
        response: {
          status: 500,
          data: { error: 'Blockchain service unavailable' }
        }
      };

      api.get.mockRejectedValue(mockError);

      await expect(getRewardPoolInfo()).rejects.toEqual(mockError);
      expect(api.get).toHaveBeenCalledWith('blockchain/reward-pool-info/');
    });

    it('should handle unauthorized access to reward pool info', async () => {
      const mockError = {
        response: {
          status: 403,
          data: { error: 'Admin access required' }
        }
      };

      api.get.mockRejectedValue(mockError);

      await expect(getRewardPoolInfo()).rejects.toEqual(mockError);
    });
  });

  describe('refillRewardPool', () => {
    it('should refill reward pool with valid amount', async () => {
      const mockResponse = {
        data: {
          transaction_hash: '0xabc123...',
          amount: '100.0',
          status: 'confirmed',
          new_pool_balance: '1100.0',
          timestamp: '2025-06-21T12:00:00Z'
        }
      };

      api.post.mockResolvedValue(mockResponse);

      const amount = '100.0';
      const result = await refillRewardPool(amount);

      expect(api.post).toHaveBeenCalledWith('blockchain/refill-reward-pool/', { amount });
      expect(result).toEqual(mockResponse);
    });

    it('should handle invalid refill amounts', async () => {
      const mockError = {
        response: {
          status: 400,
          data: { error: 'Invalid amount: must be positive number' }
        }
      };

      api.post.mockRejectedValue(mockError);

      const invalidAmount = '-10';
      
      await expect(refillRewardPool(invalidAmount)).rejects.toEqual(mockError);
      expect(api.post).toHaveBeenCalledWith('blockchain/refill-reward-pool/', { amount: invalidAmount });
    });

    it('should handle insufficient balance errors', async () => {
      const mockError = {
        response: {
          status: 400,
          data: { error: 'Insufficient admin wallet balance' }
        }
      };

      api.post.mockRejectedValue(mockError);

      const amount = '1000000';
      
      await expect(refillRewardPool(amount)).rejects.toEqual(mockError);
    });

    it('should handle blockchain network errors', async () => {
      const mockError = {
        response: {
          status: 502,
          data: { error: 'Blockchain network temporarily unavailable' }
        }
      };

      api.post.mockRejectedValue(mockError);

      const amount = '50.0';
      
      await expect(refillRewardPool(amount)).rejects.toEqual(mockError);
    });
  });

  describe('getBlockchainTransactions', () => {
    it('should fetch transactions without parameters', async () => {
      const mockResponse = {
        data: {
          results: [
            {
              id: 1,
              transaction_hash: '0xabc123...',
              transaction_type: 'reward',
              amount: '10.0',
              timestamp: '2025-06-21T10:00:00Z',
              status: 'confirmed'
            },
            {
              id: 2,
              transaction_hash: '0xdef456...',
              transaction_type: 'purchase',
              amount: '25.0',
              timestamp: '2025-06-21T09:30:00Z',
              status: 'confirmed'
            }
          ],
          count: 2,
          next: null,
          previous: null
        }
      };

      api.get.mockResolvedValue(mockResponse);

      const result = await getBlockchainTransactions();

      expect(api.get).toHaveBeenCalledWith('blockchain/transactions/', { params: {} });
      expect(result).toEqual(mockResponse);
    });

    it('should fetch transactions with pagination parameters', async () => {
      const mockResponse = {
        data: {
          results: [],
          count: 100,
          next: 'http://api.example.com/blockchain/transactions/?page=3',
          previous: 'http://api.example.com/blockchain/transactions/?page=1'
        }
      };

      api.get.mockResolvedValue(mockResponse);

      const params = { page: 2, pageSize: 10 };
      const result = await getBlockchainTransactions(params);

      expect(api.get).toHaveBeenCalledWith('blockchain/transactions/', { params });
      expect(result).toEqual(mockResponse);
    });

    it('should fetch transactions with filters', async () => {
      const mockResponse = {
        data: {
          results: [
            {
              id: 1,
              transaction_type: 'reward',
              amount: '10.0',
              timestamp: '2025-06-21T10:00:00Z'
            }
          ]
        }
      };

      api.get.mockResolvedValue(mockResponse);

      const params = {
        transactionType: 'reward',
        startDate: '2025-06-21',
        endDate: '2025-06-21'
      };
      
      const result = await getBlockchainTransactions(params);

      expect(api.get).toHaveBeenCalledWith('blockchain/transactions/', { params });
      expect(result).toEqual(mockResponse);
    });

    it('should handle transaction fetch errors', async () => {
      const mockError = {
        response: {
          status: 500,
          data: { error: 'Database connection failed' }
        }
      };

      api.get.mockRejectedValue(mockError);

      await expect(getBlockchainTransactions()).rejects.toEqual(mockError);
    });
  });

  describe('manualTeoCoinTransfer', () => {
    it('should transfer TeoCoins successfully', async () => {
      const mockResponse = {
        data: {
          transaction_hash: '0xteocoin123...',
          to_address: '0xuser456...',
          amount: '50.0',
          status: 'confirmed',
          timestamp: '2025-06-21T12:30:00Z',
          gas_used: '21000',
          gas_price: '20'
        }
      };

      api.post.mockResolvedValue(mockResponse);

      const transferData = {
        toAddress: '0xuser456...',
        amount: '50.0'
      };

      const result = await manualTeoCoinTransfer(transferData);

      expect(api.post).toHaveBeenCalledWith('blockchain/reward/', transferData);
      expect(result).toEqual(mockResponse);
    });

    it('should handle invalid recipient address', async () => {
      const mockError = {
        response: {
          status: 400,
          data: { error: 'Invalid recipient wallet address' }
        }
      };

      api.post.mockRejectedValue(mockError);

      const transferData = {
        toAddress: 'invalid-address',
        amount: '50.0'
      };

      await expect(manualTeoCoinTransfer(transferData)).rejects.toEqual(mockError);
      expect(api.post).toHaveBeenCalledWith('blockchain/reward/', transferData);
    });

    it('should handle insufficient TeoCoin balance', async () => {
      const mockError = {
        response: {
          status: 400,
          data: { error: 'Insufficient TeoCoin balance in reward pool' }
        }
      };

      api.post.mockRejectedValue(mockError);

      const transferData = {
        toAddress: '0xuser456...',
        amount: '999999.0'
      };

      await expect(manualTeoCoinTransfer(transferData)).rejects.toEqual(mockError);
    });

    it('should handle zero or negative transfer amounts', async () => {
      const mockError = {
        response: {
          status: 400,
          data: { error: 'Transfer amount must be positive' }
        }
      };

      api.post.mockRejectedValue(mockError);

      const transferData = {
        toAddress: '0xuser456...',
        amount: '0'
      };

      await expect(manualTeoCoinTransfer(transferData)).rejects.toEqual(mockError);
    });

    it('should handle blockchain transaction failures', async () => {
      const mockError = {
        response: {
          status: 502,
          data: { 
            error: 'Transaction failed on blockchain',
            details: 'Gas estimation failed'
          }
        }
      };

      api.post.mockRejectedValue(mockError);

      const transferData = {
        toAddress: '0xuser456...',
        amount: '25.0'
      };

      await expect(manualTeoCoinTransfer(transferData)).rejects.toEqual(mockError);
    });
  });

  describe('error handling scenarios', () => {
    it('should handle network connectivity issues', async () => {
      const networkError = new Error('Network Error');
      api.get.mockRejectedValue(networkError);

      await expect(getRewardPoolInfo()).rejects.toThrow('Network Error');
    });

    it('should handle timeout errors', async () => {
      const timeoutError = new Error('timeout of 10000ms exceeded');
      api.post.mockRejectedValue(timeoutError);

      const transferData = {
        toAddress: '0xuser456...',
        amount: '10.0'
      };

      await expect(manualTeoCoinTransfer(transferData)).rejects.toThrow('timeout of 10000ms exceeded');
    });

    it('should handle unauthorized blockchain operations', async () => {
      const authError = {
        response: {
          status: 401,
          data: { error: 'Authentication required for blockchain operations' }
        }
      };

      api.post.mockRejectedValue(authError);

      await expect(refillRewardPool('100.0')).rejects.toEqual(authError);
    });
  });
});
