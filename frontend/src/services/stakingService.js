/**
 * Staking Service for Frontend
 * Handles all API calls related to TeoCoin staking
 */

import api from './core/axiosClient';

class StakingService {
  /**
   * Get user's complete staking information
   */
  async getStakingInfo() {
    try {
      const response = await api.get('/services/staking/info/');
      return response.data;
    } catch (error) {
      console.error('❌ StakingService.getStakingInfo error:', error);
      console.error('Response status:', error.response?.status);
      console.error('Response data:', error.response?.data);
      
      // Handle 403 Forbidden specifically
      if (error.response?.status === 403) {
        throw new Error('Staking is only available for teachers');
      }
      
      throw new Error(error.response?.data?.error || 'Failed to fetch staking info');
    }
  }

  /**
   * Stake TEO tokens
   * @param {number} amount - Amount of TEO to stake
   */
  async stakeTokens(amount) {
    try {
      const response = await api.post('/services/staking/stake/', {
        amount: amount
      });
      return response.data;
    } catch (error) {
      // Log the full error for debugging
      console.error('Staking API Error:', {
        status: error.response?.status,
        statusText: error.response?.statusText,
        data: error.response?.data,
        url: error.config?.url,
        method: error.config?.method
      });
      
      // Extract the specific error message
      const errorMessage = error.response?.data?.error || 
                          error.response?.data?.message || 
                          error.message || 
                          'Failed to stake tokens';
      
      throw new Error(errorMessage);
    }
  }

  /**
   * Unstake TEO tokens
   * @param {number} amount - Amount of TEO to unstake
   */
  async unstakeTokens(amount) {
    try {
      const response = await api.post('/services/staking/unstake/', {
        amount: amount
      });
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.error || 'Failed to unstake tokens');
    }
  }

  /**
   * Get all staking tier configurations
   */
  async getStakingTiers() {
    try {
      const response = await api.get('/services/staking/tiers/');
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.error || 'Failed to fetch staking tiers');
    }
  }

  /**
   * Calculate commission rates and tier progression
   * @param {number} currentStake - Current staked amount
   */
  async calculateCommission(currentStake = 0) {
    try {
      const response = await api.get('/services/staking/calculator/', {
        params: { current_stake: currentStake }
      });
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.error || 'Failed to calculate commission');
    }
  }

  /**
   * Get tier benefits comparison
   */
  getTierBenefits() {
    return {
      Bronze: {
        commissionRate: 25,
        benefits: ['Basic platform access', 'Standard support'],
        color: 'secondary'
      },
      Silver: {
        commissionRate: 22,
        benefits: ['3% commission savings', 'Priority support'],
        color: 'default'
      },
      Gold: {
        commissionRate: 19,
        benefits: ['6% commission savings', 'Advanced analytics'],
        color: 'warning'
      },
      Platinum: {
        commissionRate: 16,
        benefits: ['9% commission savings', 'Premium features'],
        color: 'primary'
      },
      Diamond: {
        commissionRate: 15,
        benefits: ['10% commission savings', 'VIP support', 'All features'],
        color: 'success'
      }
    };
  }

  /**
   * Format TEO amount for display
   * @param {number} amount - TEO amount
   * @param {number} decimals - Decimal places
   */
  formatTEO(amount, decimals = 2) {
    if (amount === null || amount === undefined) return '0.00';
    return parseFloat(amount).toFixed(decimals);
  }

  /**
   * Calculate potential savings from tier upgrade
   * @param {number} currentTier - Current tier index
   * @param {number} targetTier - Target tier index
   */
  calculateSavings(currentTier, targetTier) {
    const tierRates = [25, 22, 19, 16, 15]; // Commission rates by tier
    
    if (currentTier >= targetTier || targetTier >= tierRates.length) {
      return 0;
    }
    
    const currentRate = tierRates[currentTier];
    const targetRate = tierRates[targetTier];
    
    return currentRate - targetRate;
  }

  /**
   * Check if user can afford a stake amount
   * @param {number} amount - Amount to stake
   * @param {number} balance - User's TEO balance
   */
  canAffordStake(amount, balance) {
    return parseFloat(amount) > 0 && parseFloat(amount) <= parseFloat(balance);
  }

  /**
   * Get recommended staking amounts for tier upgrades
   * @param {number} currentStake - Current staked amount
   */
  getRecommendedAmounts(currentStake) {
    const tierRequirements = [0, 100, 300, 600, 1000];
    const recommendations = [];
    
    for (let i = 0; i < tierRequirements.length; i++) {
      const required = tierRequirements[i];
      if (required > currentStake) {
        recommendations.push({
          tier: i,
          tierName: ['Bronze', 'Silver', 'Gold', 'Platinum', 'Diamond'][i],
          requiredAmount: required,
          additionalAmount: required - currentStake,
          commissionRate: [25, 22, 19, 16, 15][i]
        });
      }
    }
    
    return recommendations;
  }
}

export const stakingService = new StakingService();
export default stakingService;
