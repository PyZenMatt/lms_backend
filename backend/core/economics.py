"""
SchoolPlatform Economic Configuration
Centralized settings for platform economics and commission structure
"""

from decimal import Decimal
from django.conf import settings

class PlatformEconomics:
    """
    Central configuration for platform economics and commission structure
    """
    
    # PLATFORM COMMISSION STRUCTURE
    PLATFORM_COMMISSION_RATE = Decimal('0.25')      # 25% platform commission
    TEACHER_PAYOUT_RATE = Decimal('0.75')           # 75% to teachers
    PAYMENT_PROCESSING_FEE = Decimal('0.03')        # ~3% Stripe fees
    
    # TEOCOIN REWARD SYSTEM
    TEOCOIN_REWARD_POOL_RATE = Decimal('0.05')      # 5% of platform commission goes to rewards
    TEOCOIN_EURO_EXCHANGE_RATE = Decimal('0.50')    # 1 TEO = €0.50 for discounts
    
    # DISCOUNT LIMITS
    MAX_DISCOUNT_PERCENTAGE = Decimal('0.20')       # Max 20% discount per course
    MIN_TEOCOIN_FOR_DISCOUNT = Decimal('2.0')       # Minimum 2 TEO required
    
    # TEOCOIN REWARD RATES
    COURSE_COMPLETION_REWARD_RATE = Decimal('0.10')  # 10% of course price as TEO reward
    COURSE_PURCHASE_REWARD_RATE = Decimal('0.05')    # 5% of course price as TEO reward
    
    # COMPETITOR COMPARISON DATA
    UDEMY_AVERAGE_INSTRUCTOR_SHARE = Decimal('0.50')    # 37-97% average
    SKILLSHARE_INSTRUCTOR_SHARE = Decimal('0.30')       # ~30%
    COURSERA_INSTRUCTOR_SHARE = Decimal('0.50')         # 40-60% average
    
    # OUR COMPETITIVE ADVANTAGE
    OUR_ADVANTAGE_VS_UDEMY = TEACHER_PAYOUT_RATE - UDEMY_AVERAGE_INSTRUCTOR_SHARE
    OUR_ADVANTAGE_VS_SKILLSHARE = TEACHER_PAYOUT_RATE - SKILLSHARE_INSTRUCTOR_SHARE
    OUR_ADVANTAGE_VS_COURSERA = TEACHER_PAYOUT_RATE - COURSERA_INSTRUCTOR_SHARE

    # TEOCOIN STAKING SYSTEM
    STAKING_TIERS = {
        'bronze': {'teo_required': Decimal('0'), 'commission_rate': Decimal('0.25'), 'teacher_rate': Decimal('0.75')},
        'silver': {'teo_required': Decimal('500'), 'commission_rate': Decimal('0.22'), 'teacher_rate': Decimal('0.78')},
        'gold': {'teo_required': Decimal('1500'), 'commission_rate': Decimal('0.19'), 'teacher_rate': Decimal('0.81')},
        'platinum': {'teo_required': Decimal('3000'), 'commission_rate': Decimal('0.16'), 'teacher_rate': Decimal('0.84')},
        'diamond': {'teo_required': Decimal('5000'), 'commission_rate': Decimal('0.15'), 'teacher_rate': Decimal('0.85')},
    }
    
    # TEO COMPENSATION FOR ABSORBING DISCOUNTS
    DISCOUNT_ABSORPTION_MULTIPLIER = Decimal('1.25')  # 125% TEO compensation
    
    @classmethod
    def calculate_course_economics(cls, course_price_eur: Decimal) -> dict:
        """
        Calculate complete economics for a course sale
        
        Args:
            course_price_eur: Course price in EUR
            
        Returns:
            dict: Complete breakdown of course economics
        """
        
        # Basic calculations
        platform_commission = course_price_eur * cls.PLATFORM_COMMISSION_RATE
        teacher_payout = course_price_eur * cls.TEACHER_PAYOUT_RATE
        payment_fee = course_price_eur * cls.PAYMENT_PROCESSING_FEE
        teocoin_reward_pool = platform_commission * cls.TEOCOIN_REWARD_POOL_RATE
        platform_net = platform_commission - payment_fee - teocoin_reward_pool
        
        # TeoCoin rewards
        purchase_reward_teo = course_price_eur * cls.COURSE_PURCHASE_REWARD_RATE
        completion_reward_teo = course_price_eur * cls.COURSE_COMPLETION_REWARD_RATE
        total_teo_rewards = purchase_reward_teo + completion_reward_teo
        
        # Discount calculations
        max_discount_eur = course_price_eur * cls.MAX_DISCOUNT_PERCENTAGE
        teo_needed_for_max_discount = max_discount_eur / cls.TEOCOIN_EURO_EXCHANGE_RATE
        
        return {
            'course_price_eur': float(course_price_eur),
            'teacher_payout_eur': float(teacher_payout),
            'platform_commission_eur': float(platform_commission),
            'payment_processing_fee_eur': float(payment_fee),
            'teocoin_reward_pool_eur': float(teocoin_reward_pool),
            'platform_net_revenue_eur': float(platform_net),
            
            # TeoCoin rewards
            'purchase_reward_teo': float(purchase_reward_teo),
            'completion_reward_teo': float(completion_reward_teo),
            'total_teo_rewards': float(total_teo_rewards),
            
            # Discount info
            'max_discount_eur': float(max_discount_eur),
            'teo_needed_for_max_discount': float(teo_needed_for_max_discount),
            'max_discount_percentage': float(cls.MAX_DISCOUNT_PERCENTAGE * 100),
            
            # Rates
            'platform_commission_rate': float(cls.PLATFORM_COMMISSION_RATE * 100),
            'teacher_payout_rate': float(cls.TEACHER_PAYOUT_RATE * 100),
            'teo_euro_exchange_rate': float(cls.TEOCOIN_EURO_EXCHANGE_RATE),
        }
    
    @classmethod
    def get_discount_with_teo(cls, course_price_eur: Decimal, teo_to_spend: Decimal) -> dict:
        """
        Calculate final price when applying TeoCoin discount
        
        Args:
            course_price_eur: Original course price
            teo_to_spend: Amount of TeoCoin to spend
            
        Returns:
            dict: Discount calculation results
        """
        
        # Calculate discount
        discount_eur = teo_to_spend * cls.TEOCOIN_EURO_EXCHANGE_RATE
        max_allowed_discount = course_price_eur * cls.MAX_DISCOUNT_PERCENTAGE
        
        # Apply limits
        actual_discount = min(discount_eur, max_allowed_discount)
        final_price = course_price_eur - actual_discount
        discount_percentage = (actual_discount / course_price_eur) * 100
        
        # Recalculate economics with discount
        economics = cls.calculate_course_economics(final_price)
        
        return {
            'original_price_eur': float(course_price_eur),
            'teo_spent': float(teo_to_spend),
            'discount_applied_eur': float(actual_discount),
            'final_price_eur': float(final_price),
            'discount_percentage': float(discount_percentage),
            'savings_message': f'Save €{actual_discount:.2f} with {teo_to_spend} TEO',
            'economics': economics  # Updated economics based on final price
        }
    
    @classmethod
    def compare_annual_earnings(cls, monthly_sales: int, avg_course_price: Decimal) -> dict:
        """
        Compare annual earnings between SchoolPlatform and competitors
        
        Args:
            monthly_sales: Number of courses sold per month
            avg_course_price: Average course price in EUR
            
        Returns:
            dict: Annual earnings comparison across platforms
        """
        
        annual_gross = monthly_sales * 12 * avg_course_price
        
        # Calculate annual earnings on each platform
        schoolplatform_annual = annual_gross * cls.TEACHER_PAYOUT_RATE
        udemy_annual = annual_gross * cls.UDEMY_AVERAGE_INSTRUCTOR_SHARE
        skillshare_annual = annual_gross * cls.SKILLSHARE_INSTRUCTOR_SHARE
        coursera_annual = annual_gross * cls.COURSERA_INSTRUCTOR_SHARE
        
        return {
            'monthly_sales': monthly_sales,
            'avg_course_price_eur': float(avg_course_price),
            'annual_gross_revenue_eur': float(annual_gross),
            
            'schoolplatform_annual_eur': float(schoolplatform_annual),
            'udemy_annual_eur': float(udemy_annual),
            'skillshare_annual_eur': float(skillshare_annual),
            'coursera_annual_eur': float(coursera_annual),
            
            'advantage_vs_udemy_eur': float(schoolplatform_annual - udemy_annual),
            'advantage_vs_skillshare_eur': float(schoolplatform_annual - skillshare_annual),
            'advantage_vs_coursera_eur': float(schoolplatform_annual - coursera_annual),
            
            'advantage_vs_udemy_percent': float(cls.OUR_ADVANTAGE_VS_UDEMY * 100),
            'advantage_vs_skillshare_percent': float(cls.OUR_ADVANTAGE_VS_SKILLSHARE * 100),
            'advantage_vs_coursera_percent': float(cls.OUR_ADVANTAGE_VS_COURSERA * 100),
        }

    @classmethod
    def get_teacher_tier(cls, teo_staked: Decimal) -> dict:
        """
        Determine teacher's staking tier based on TEO staked
        
        Args:
            teo_staked: Amount of TEO the teacher has staked
            
        Returns:
            dict: Tier information including commission rates
        """
        for tier_name in ['diamond', 'platinum', 'gold', 'silver', 'bronze']:
            tier_info = cls.STAKING_TIERS[tier_name]
            if teo_staked >= tier_info['teo_required']:
                return {
                    'tier_name': tier_name,
                    'teo_required': float(tier_info['teo_required']),
                    'commission_rate': float(tier_info['commission_rate']),
                    'teacher_rate': float(tier_info['teacher_rate']),
                    'teo_staked': float(teo_staked)
                }
        
        # Fallback to bronze
        return {
            'tier_name': 'bronze',
            'teo_required': 0,
            'commission_rate': 0.25,
            'teacher_rate': 0.75,
            'teo_staked': float(teo_staked)
        }
    
    @classmethod
    def calculate_staking_economics(cls, course_price_eur: Decimal, teacher_teo_staked: Decimal = Decimal('0')) -> dict:
        """
        Calculate course economics including teacher staking benefits
        
        Args:
            course_price_eur: Course price in EUR
            teacher_teo_staked: Amount of TEO teacher has staked
            
        Returns:
            dict: Complete economics including staking benefits
        """
        
        # Get teacher tier
        tier_info = cls.get_teacher_tier(teacher_teo_staked)
        
        # Calculate with staking rates
        commission_rate = Decimal(str(tier_info['commission_rate']))
        teacher_rate = Decimal(str(tier_info['teacher_rate']))
        
        platform_commission = course_price_eur * commission_rate
        teacher_payout = course_price_eur * teacher_rate
        payment_fee = course_price_eur * cls.PAYMENT_PROCESSING_FEE
        teocoin_reward_pool = platform_commission * cls.TEOCOIN_REWARD_POOL_RATE
        platform_net = platform_commission - payment_fee - teocoin_reward_pool
        
        # Calculate benefits vs bronze tier
        bronze_commission = course_price_eur * cls.STAKING_TIERS['bronze']['commission_rate']
        bronze_teacher = course_price_eur * cls.STAKING_TIERS['bronze']['teacher_rate']
        staking_benefit = teacher_payout - bronze_teacher
        
        return {
            'course_price_eur': float(course_price_eur),
            'teacher_payout_eur': float(teacher_payout),
            'platform_commission_eur': float(platform_commission),
            'payment_processing_fee_eur': float(payment_fee),
            'teocoin_reward_pool_eur': float(teocoin_reward_pool),
            'platform_net_revenue_eur': float(platform_net),
            
            # Staking info
            'staking_tier': tier_info['tier_name'],
            'teo_staked': float(teacher_teo_staked),
            'commission_rate_percent': float(commission_rate * 100),
            'teacher_rate_percent': float(teacher_rate * 100),
            'monthly_staking_benefit_eur': float(staking_benefit),
            'annual_staking_benefit_eur': float(staking_benefit * 12),
            
            # Comparison to bronze
            'bronze_teacher_payout_eur': float(bronze_teacher),
            'staking_advantage_eur': float(staking_benefit),
            'staking_advantage_percent': float((staking_benefit / bronze_teacher) * 100) if bronze_teacher > 0 else 0,
        }

# Global instance for easy imports
platform_economics = PlatformEconomics()
