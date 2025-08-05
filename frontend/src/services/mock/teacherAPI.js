/**
 * 🔧 Mock Teacher/Staking API Service
 * 
 * Provides mock teacher and staking data when backend endpoints are not available
 */

export const mockTeacherAPI = {
  /**
   * Mock staking info endpoint
   */
  async getStakingInfo() {
    // Simulate network delay
    await new Promise(resolve => setTimeout(resolve, 800));
    
    return {
      ok: true,
      status: 200,
      json: () => Promise.resolve({
        success: true,
        staking_info: {
          total_staked: 1250.0,
          current_tier: 'Gold',
          tier_benefits: {
            commission_rate: 0.15,
            priority_support: true,
            advanced_analytics: true,
            custom_branding: true
          },
          staking_periods: [
            {
              id: 1,
              amount: 500.0,
              start_date: '2024-01-15',
              end_date: '2024-07-15',
              status: 'active',
              projected_rewards: 75.0
            },
            {
              id: 2,
              amount: 750.0,
              start_date: '2024-03-01',
              end_date: '2024-09-01',
              status: 'active',
              projected_rewards: 112.5
            }
          ],
          total_projected_rewards: 187.5,
          next_tier: 'Platinum',
          next_tier_requirement: 2000.0,
          progress_to_next_tier: 0.625
        }
      })
    };
  },

  /**
   * Mock balance endpoint
   */
  async getBalance() {
    // Simulate network delay
    await new Promise(resolve => setTimeout(resolve, 600));
    
    return {
      ok: true,
      status: 200,
      json: () => Promise.resolve({
        success: true,
        balance: {
          available: 2847.50,
          staked: 1250.0,
          pending_rewards: 187.5,
          total: 4285.0,
          last_updated: new Date().toISOString()
        }
      })
    };
  },

  /**
   * Mock teacher profile
   */
  async getTeacherProfile() {
    await new Promise(resolve => setTimeout(resolve, 500));
    
    return {
      ok: true,
      status: 200,
      json: () => Promise.resolve({
        success: true,
        teacher: {
          id: 1,
          name: 'Prof. Marco Rossi',
          email: 'marco.rossi@example.com',
          specialization: 'Web Development',
          experience_years: 5,
          total_students: 248,
          courses_taught: 12,
          average_rating: 4.8,
          total_reviews: 156,
          verification_status: 'verified',
          achievements: [
            'Top Rated Teacher',
            'Student Favorite',
            'Innovation Award 2024'
          ],
          stats: {
            total_earnings: 15430.50,
            active_courses: 3,
            completed_courses: 9,
            response_time: '< 2 hours'
          }
        }
      })
    };
  },

  /**
   * Mock staking transaction
   */
  async stakeTokens(amount) {
    await new Promise(resolve => setTimeout(resolve, 2000));
    
    if (amount < 100) {
      throw new Error('Minimum stake amount is 100 TeoCoins');
    }
    
    return {
      ok: true,
      status: 200,
      json: () => Promise.resolve({
        success: true,
        transaction: {
          id: `stake_${Date.now()}`,
          amount: amount,
          status: 'confirmed',
          timestamp: new Date().toISOString(),
          gas_fee: 0.05,
          estimated_rewards: amount * 0.15 // 15% APY
        },
        message: `Successfully staked ${amount} TeoCoins`
      })
    };
  },

  /**
   * Mock unstaking transaction
   */
  async unstakeTokens(stakingId) {
    await new Promise(resolve => setTimeout(resolve, 1500));
    
    return {
      ok: true,
      status: 200,
      json: () => Promise.resolve({
        success: true,
        transaction: {
          id: `unstake_${Date.now()}`,
          staking_id: stakingId,
          status: 'confirmed',
          timestamp: new Date().toISOString(),
          cooldown_period: '7 days',
          available_date: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString()
        },
        message: 'Unstaking initiated. Tokens will be available after cooldown period.'
      })
    };
  },

  /**
   * Mock earnings history
   */
  async getEarningsHistory() {
    await new Promise(resolve => setTimeout(resolve, 700));
    
    const earnings = [];
    const now = new Date();
    
    for (let i = 0; i < 30; i++) {
      const date = new Date(now.getTime() - (i * 24 * 60 * 60 * 1000));
      earnings.push({
        date: date.toISOString().split('T')[0],
        course_earnings: Math.random() * 50 + 10,
        staking_rewards: Math.random() * 20 + 5,
        bonus_earnings: Math.random() * 15,
        total: 0
      });
      
      // Calculate total
      const last = earnings[earnings.length - 1];
      last.total = last.course_earnings + last.staking_rewards + last.bonus_earnings;
    }
    
    return {
      ok: true,
      status: 200,
      json: () => Promise.resolve({
        success: true,
        earnings: earnings.reverse(),
        summary: {
          total_this_month: earnings.reduce((sum, e) => sum + e.total, 0),
          average_daily: earnings.reduce((sum, e) => sum + e.total, 0) / earnings.length,
          best_day: Math.max(...earnings.map(e => e.total)),
          growth_rate: 0.15
        }
      })
    };
  }
};

export default mockTeacherAPI;
