"""
Tier-based splits calculation for Payment Discount Snapshots
R1.2 Implementation - Policy-based EUR/TEO splits
"""
from decimal import Decimal
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


def get_teacher_tier_splits(teacher) -> Dict[str, Decimal]:
    """
    Get teacher tier split percentages from profile.
    Returns {'teacher_split': %, 'platform_split': %} 
    Fallback to Bronze 50/50 if tier not found.
    """
    try:
        # Try to get tier from teacher profile
        teacher_profile = getattr(teacher, 'teacher_profile', None)
        if teacher_profile and hasattr(teacher_profile, 'staking_tier'):
            tier_name = teacher_profile.staking_tier
            
            # Tier lookup table (can be moved to DB later)
            tier_splits = {
                'Wood': {'teacher': Decimal('40'), 'platform': Decimal('60')},
                'Bronze': {'teacher': Decimal('50'), 'platform': Decimal('50')}, 
                'Silver': {'teacher': Decimal('55'), 'platform': Decimal('45')},
                'Gold': {'teacher': Decimal('65'), 'platform': Decimal('35')},
                'Diamond': {'teacher': Decimal('70'), 'platform': Decimal('30')},
            }
            
            if tier_name in tier_splits:
                splits = tier_splits[tier_name]
                return {
                    'teacher_split': splits['teacher'],
                    'platform_split': splits['platform']
                }
        
        # Fallback to Bronze
        logger.warning(f"No tier found for teacher {teacher.id}, defaulting to Bronze 50/50")
        return {'teacher_split': Decimal('50'), 'platform_split': Decimal('50')}
        
    except Exception as e:
        logger.warning(f"Error getting tier for teacher {teacher.id}: {e}, defaulting to Bronze")
        return {'teacher_split': Decimal('50'), 'platform_split': Decimal('50')}


def calculate_splits_by_policy(course_price: Decimal, teacher, discount_amount: Decimal) -> Dict[str, Any]:
    """
    Calculate EUR/TEO splits according to policy.
    
    Args:
        course_price: Course price in EUR
        teacher: Teacher user object
        discount_amount: TEO discount amount in EUR (1 TEO = 1 EUR)
        
    Returns:
        Dict with splits for both options A (refuse) and B (accept)
    """
    try:
        # Get tier-based splits
        tier_splits = get_teacher_tier_splits(teacher)
        teacher_pct = tier_splits['teacher_split'] / Decimal('100')
        platform_pct = tier_splits['platform_split'] / Decimal('100')
        
        # Option A (Teacher refuses TEO) 
        teacher_eur_a = course_price * teacher_pct
        platform_eur_a = course_price * platform_pct - discount_amount
        platform_teo_a = discount_amount  # Platform gets the TEO
        
        # Option B (Teacher accepts TEO)
        teacher_eur_b = course_price * teacher_pct - discount_amount
        teacher_teo_b = discount_amount * Decimal('1.25')  # 25% bonus
        platform_eur_b = course_price * platform_pct
        platform_teo_b = Decimal('0')  # No TEO for platform
        
        return {
            'tier_name': getattr(teacher, 'teacher_profile', {}).get('staking_tier', 'Bronze'),
            'teacher_split_pct': tier_splits['teacher_split'],
            'platform_split_pct': tier_splits['platform_split'],
            'option_a': {
                'teacher_eur': teacher_eur_a,
                'platform_eur': platform_eur_a,
                'teacher_teo': Decimal('0'),
                'platform_teo': platform_teo_a,
            },
            'option_b': {
                'teacher_eur': teacher_eur_b, 
                'teacher_teo': teacher_teo_b,
                'platform_eur': platform_eur_b,
                'platform_teo': platform_teo_b,
            }
        }
        
    except Exception as e:
        logger.error(f"Error calculating splits: {e}")
        # Return safe defaults
        return {
            'tier_name': 'Bronze',
            'teacher_split_pct': Decimal('50'),
            'platform_split_pct': Decimal('50'),
            'option_a': {
                'teacher_eur': course_price * Decimal('0.5'),
                'platform_eur': course_price * Decimal('0.5') - discount_amount,
                'teacher_teo': Decimal('0'),
                'platform_teo': discount_amount,
            },
            'option_b': {
                'teacher_eur': course_price * Decimal('0.5') - discount_amount,
                'teacher_teo': discount_amount * Decimal('1.25'),
                'platform_eur': course_price * Decimal('0.5'),
                'platform_teo': Decimal('0'),
            }
        }
