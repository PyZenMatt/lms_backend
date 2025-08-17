"""
Database-Only Staking API Views

Provides REST API endpoints for the new database-only staking system.
This replaces blockchain staking with an instant, platform-internal system.
"""

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import get_user_model
from django.db import transaction
from decimal import Decimal
import logging

from blockchain.models import DBTeoCoinBalance, DBTeoCoinTransaction
from users.models import TeacherProfile

User = get_user_model()
logger = logging.getLogger(__name__)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_staking_info(request):
    """
    Get complete staking information for the authenticated teacher
    
    Only teachers can access staking functionality.
    
    Returns:
        - current_balance: Available TEO balance
        - staked_amount: Currently staked TEO
        - tier: Current staking tier
        - commission_rate: Current commission rate
        - next_tier_requirement: TEO needed for next tier
    """
    try:
        user = request.user
        
        # Check if user is a teacher
        if user.role != 'teacher':
            return Response({
                'success': False,
                'error': 'Staking is only available for teachers. Students cannot stake TEO tokens.'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Get or create DB TeoCoin balance
        teo_balance, created = DBTeoCoinBalance.objects.get_or_create(
            user=user,
            defaults={
                'available_balance': Decimal('0.00'),
                'staked_balance': Decimal('0.00')
            }
        )
        
        # Get or create teacher profile (for commission rates)
        teacher_profile, created = TeacherProfile.objects.get_or_create(
            user=user,
            defaults={
                'commission_rate': Decimal('50.00'),
                'staking_tier': 'Bronze',
                'staked_teo_amount': Decimal('0.00')
            }
        )
        
        # Sync staked amount between models
        if teacher_profile.staked_teo_amount != teo_balance.staked_balance:
            teacher_profile.staked_teo_amount = teo_balance.staked_balance
            teacher_profile.update_tier_and_commission()
            teacher_profile.save()
        
        # Calculate next tier requirement
        tier_requirements = {
            'Bronze': Decimal('100.00'),
            'Silver': Decimal('300.00'), 
            'Gold': Decimal('600.00'),
            'Platinum': Decimal('1000.00'),
            'Diamond': None  # Max tier
        }
        
        next_tier_requirement = tier_requirements.get(teacher_profile.staking_tier)
        next_tier_needed = None
        if next_tier_requirement:
            next_tier_needed = max(0, next_tier_requirement - teo_balance.staked_balance)
        
        return Response({
            'success': True,
            'current_balance': float(teo_balance.available_balance),
            'staked_amount': float(teo_balance.staked_balance),
            'total_balance': float(teo_balance.total_balance),
            'tier': teacher_profile.staking_tier,
            'commission_rate': float(teacher_profile.commission_rate),
            'teacher_earnings_percentage': float(teacher_profile.teacher_earnings_percentage),
            'next_tier_requirement': float(next_tier_requirement) if next_tier_requirement else None,
            'next_tier_needed': float(next_tier_needed) if next_tier_needed else 0,
            'can_upgrade': next_tier_needed == 0 if next_tier_needed is not None else False
        })
        
    except Exception as e:
        logger.error(f"Error getting staking info for {request.user.email}: {str(e)}")
        return Response({
            'success': False,
            'error': f'Failed to get staking information: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def stake_tokens(request):
    """
    Stake TEO tokens from available balance (Teachers only)
    
    Body:
        amount (float): Amount of TEO to stake
    """
    try:
        user = request.user
        
        # Check if user is a teacher
        if user.role != 'teacher':
            return Response({
                'success': False,
                'error': 'Staking is only available for teachers. Students cannot stake TEO tokens.'
            }, status=status.HTTP_403_FORBIDDEN)
        
        amount = Decimal(str(request.data.get('amount', 0)))
        
        if amount <= 0:
            return Response({
                'success': False,
                'error': 'Amount must be greater than zero'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        with transaction.atomic():
            # Get user's TeoCoin balance
            teo_balance = DBTeoCoinBalance.objects.select_for_update().get(user=user)
            
            # Check if user has enough available balance
            if teo_balance.available_balance < amount:
                return Response({
                    'success': False,
                    'error': f'Insufficient balance. Available: {teo_balance.available_balance} TEO'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Move from available to staked
            teo_balance.available_balance -= amount
            teo_balance.staked_balance += amount
            teo_balance.save()
            
            # Update teacher profile
            teacher_profile = TeacherProfile.objects.get(user=user)
            teacher_profile.staked_teo_amount = teo_balance.staked_balance
            
            # Update tier and commission based on new stake
            old_tier = teacher_profile.staking_tier
            tier_info = teacher_profile.update_tier_and_commission()
            teacher_profile.save()
            
            # Record transaction
            DBTeoCoinTransaction.objects.create(
                user=user,
                transaction_type='staked',
                amount=amount,
                description=f'Staked {amount} TEO. Tier: {old_tier} → {tier_info["tier"]}'
            )
            
            logger.info(f"User {user.email} staked {amount} TEO. New tier: {tier_info['tier']}")
            
            return Response({
                'success': True,
                'message': f'Successfully staked {amount} TEO',
                'new_available_balance': float(teo_balance.available_balance),
                'new_staked_balance': float(teo_balance.staked_balance),
                'new_tier': tier_info['tier'],
                'new_commission_rate': float(tier_info['commission_rate']),
                'tier_upgraded': old_tier != tier_info['tier']
            })
            
    except DBTeoCoinBalance.DoesNotExist:
        return Response({
            'success': False,
            'error': 'TeoCoin balance not found. Please contact support.'
        }, status=status.HTTP_404_NOT_FOUND)
    except TeacherProfile.DoesNotExist:
        return Response({
            'success': False,
            'error': 'Teacher profile not found. Please contact support.'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Error staking tokens for {request.user.email}: {str(e)}")
        return Response({
            'success': False,
            'error': f'Failed to stake tokens: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def unstake_tokens(request):
    """
    Unstake TEO tokens back to available balance (Teachers only)
    
    Body:
        amount (float): Amount of TEO to unstake
    """
    try:
        user = request.user
        
        # Check if user is a teacher
        if user.role != 'teacher':
            return Response({
                'success': False,
                'error': 'Staking is only available for teachers. Students cannot unstake TEO tokens.'
            }, status=status.HTTP_403_FORBIDDEN)
        
        amount = Decimal(str(request.data.get('amount', 0)))
        
        if amount <= 0:
            return Response({
                'success': False,
                'error': 'Amount must be greater than zero'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        with transaction.atomic():
            # Get user's TeoCoin balance
            teo_balance = DBTeoCoinBalance.objects.select_for_update().get(user=user)
            
            # Check if user has enough staked balance
            if teo_balance.staked_balance < amount:
                return Response({
                    'success': False,
                    'error': f'Insufficient staked balance. Staked: {teo_balance.staked_balance} TEO'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Move from staked to available
            teo_balance.staked_balance -= amount
            teo_balance.available_balance += amount
            teo_balance.save()
            
            # Update teacher profile
            teacher_profile = TeacherProfile.objects.get(user=user)
            teacher_profile.staked_teo_amount = teo_balance.staked_balance
            
            # Update tier and commission based on new stake
            old_tier = teacher_profile.staking_tier
            tier_info = teacher_profile.update_tier_and_commission()
            teacher_profile.save()
            
            # Record transaction
            DBTeoCoinTransaction.objects.create(
                user=user,
                transaction_type='unstaked',
                amount=amount,
                description=f'Unstaked {amount} TEO. Tier: {old_tier} → {tier_info["tier"]}'
            )
            
            logger.info(f"User {user.email} unstaked {amount} TEO. New tier: {tier_info['tier']}")
            
            return Response({
                'success': True,
                'message': f'Successfully unstaked {amount} TEO',
                'new_available_balance': float(teo_balance.available_balance),
                'new_staked_balance': float(teo_balance.staked_balance),
                'new_tier': tier_info['tier'],
                'new_commission_rate': float(tier_info['commission_rate']),
                'tier_downgraded': old_tier != tier_info['tier']
            })
            
    except DBTeoCoinBalance.DoesNotExist:
        return Response({
            'success': False,
            'error': 'TeoCoin balance not found. Please contact support.'
        }, status=status.HTTP_404_NOT_FOUND)
    except TeacherProfile.DoesNotExist:
        return Response({
            'success': False,
            'error': 'Teacher profile not found. Please contact support.'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Error unstaking tokens for {request.user.email}: {str(e)}")
        return Response({
            'success': False,
            'error': f'Failed to unstake tokens: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def get_staking_tiers(request):
    """
    Get all staking tier configurations
    No authentication required - public information
    """
    try:
        tiers = {
            'Bronze': {
                'min_stake': 0,
                'commission_rate': 50.0,
                'teacher_earnings': 50.0,
                'color': 'secondary',
                'benefits': ['Basic platform access', 'Standard support'],
                'description': 'Starting tier for all teachers'
            },
            'Silver': {
                'min_stake': 100.0,
                'commission_rate': 45.0,
                'teacher_earnings': 55.0,
                'color': 'default',
                'benefits': ['5% higher earnings', 'Priority support'],
                'description': 'Enhanced earnings and support'
            },
            'Gold': {
                'min_stake': 300.0,
                'commission_rate': 40.0,
                'teacher_earnings': 60.0,
                'color': 'warning',
                'benefits': ['10% higher earnings', 'Advanced analytics'],
                'description': 'Premium features and analytics'
            },
            'Platinum': {
                'min_stake': 600.0,
                'commission_rate': 35.0,
                'teacher_earnings': 65.0,
                'color': 'primary',
                'benefits': ['15% higher earnings', 'Premium features'],
                'description': 'All premium features unlocked'
            },
            'Diamond': {
                'min_stake': 1000.0,
                'commission_rate': 25.0,
                'teacher_earnings': 75.0,
                'color': 'success',
                'benefits': ['25% higher earnings', 'VIP support', 'All features'],
                'description': 'Maximum tier with VIP treatment'
            }
        }
        
        return Response({
            'success': True,
            'tiers': tiers
        })
        
    except Exception as e:
        logger.error(f"Error getting staking tiers: {str(e)}")
        return Response({
            'success': False,
            'error': f'Failed to get staking tiers: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def calculate_commission(request):
    """
    Calculate commission rates and tier progression
    
    Query params:
        current_stake (float): Current staked amount
    """
    try:
        current_stake = Decimal(str(request.GET.get('current_stake', 0)))
        
        # Define tier thresholds
        tiers = [
            ('Bronze', 0, 50.0),
            ('Silver', 100, 45.0), 
            ('Gold', 300, 40.0),
            ('Platinum', 600, 35.0),
            ('Diamond', 1000, 25.0)
        ]
        
        # Find current tier
        current_tier = 'Bronze'
        current_commission = 50.0
        
        for tier_name, min_stake, commission_rate in reversed(tiers):
            if current_stake >= min_stake:
                current_tier = tier_name
                current_commission = commission_rate
                break
        
        # Calculate next tier
        next_tier = None
        next_tier_requirement = None
        next_tier_commission = None
        
        for tier_name, min_stake, commission_rate in tiers:
            if min_stake > current_stake:
                next_tier = tier_name
                next_tier_requirement = min_stake
                next_tier_commission = commission_rate
                break
        
        return Response({
            'success': True,
            'current_stake': float(current_stake),
            'current_tier': current_tier,
            'current_commission_rate': current_commission,
            'current_teacher_earnings': 100.0 - current_commission,
            'next_tier': next_tier,
            'next_tier_requirement': float(next_tier_requirement) if next_tier_requirement else None,
            'next_tier_commission': next_tier_commission,
            'next_tier_teacher_earnings': 100.0 - next_tier_commission if next_tier_commission else None,
            'additional_stake_needed': float(next_tier_requirement - current_stake) if next_tier_requirement else 0
        })
        
    except Exception as e:
        logger.error(f"Error calculating commission: {str(e)}")
        return Response({
            'success': False,
            'error': f'Failed to calculate commission: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
