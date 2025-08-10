"""
DB TeoCoin API Views
REST API endpoints for the new database-based TeoCoin system
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from decimal import Decimal
from django.db import transaction
import logging

from services.db_teocoin_service import DBTeoCoinService
from blockchain.models import DBTeoCoinBalance, TeoCoinWithdrawalRequest

logger = logging.getLogger(__name__)


class TeoCoinBalanceView(APIView):
    """Get user's DB TeoCoin balance"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get current user's TeoCoin balance"""
        try:
            db_service = DBTeoCoinService()
            balance_data = db_service.get_user_balance(request.user)
            
            return Response({
                'success': True,
                'balance': balance_data
            })
            
        except Exception as e:
            logger.error(f"Error getting balance for user {request.user.id}: {e}")
            return Response({
                'success': False,
                'error': 'Failed to get balance'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CalculateDiscountView(APIView):
    """Calculate discount for a course"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """Calculate discount based on user's balance and course price"""
        try:
            course_price = Decimal(str(request.data.get('course_price', 0)))
            course_id = request.data.get('course_id')
            
            if course_price <= 0:
                return Response({
                    'success': False,
                    'error': 'Invalid course price'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            db_service = DBTeoCoinService()
            discount_info = db_service.calculate_discount(
                user=request.user,
                course_price=course_price
            )
            
            return Response({
                'success': True,
                'discount': discount_info
            })
            
        except Exception as e:
            logger.error(f"Error calculating discount for user {request.user.id}: {e}")
            return Response({
                'success': False,
                'error': 'Failed to calculate discount'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ApplyDiscountView(APIView):
    """Apply TeoCoin discount for course purchase"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """Apply TeoCoin discount"""
        try:
            course_id = request.data.get('course_id')
            teo_amount = Decimal(str(request.data.get('teo_amount', '0')))
            discount_percentage = Decimal(str(request.data.get('discount_percentage', '0')))
            
            if not course_id or teo_amount <= 0:
                return Response({
                    'success': False,
                    'error': 'Course ID and TeoCoin amount required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Check user balance
            db_service = DBTeoCoinService()
            balance = db_service.get_user_balance(request.user)
            if balance['available_balance'] < teo_amount:
                return Response({
                    'success': False,
                    'error': f'Insufficient balance. Available: {balance["available_balance"]} TEO, Required: {teo_amount} TEO'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Deduct TeoCoin for discount
            success = db_service.deduct_balance(
                user=request.user,
                amount=teo_amount,
                transaction_type='discount',
                description=f'Discount applied for course {course_id}',
                course_id=course_id
            )
            
            if not success:
                return Response({
                    'success': False,
                    'error': 'Failed to apply discount'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Get updated balance
            new_balance_data = db_service.get_user_balance(request.user)
            
            return Response({
                'success': True,
                'message': 'Discount applied successfully',
                'teo_used': float(teo_amount),
                'new_balance': float(new_balance_data['available_balance']),
                'discount_percentage': float(discount_percentage)
            })
            
        except Exception as e:
            logger.error(f"Error applying TeoCoin discount: {e}")
            return Response({
                'success': False,
                'error': 'Failed to apply discount'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class PurchaseCourseView(APIView):
    """Purchase course entirely with TeoCoin"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """Purchase course with TeoCoin"""
        try:
            course_id = request.data.get('course_id')
            teo_amount = Decimal(str(request.data.get('teo_amount', '0')))
            
            if not course_id or teo_amount <= 0:
                return Response({
                    'success': False,
                    'error': 'Course ID and TeoCoin amount required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Check user balance
            balance = hybrid_teocoin_service.get_user_balance(request.user)
            if balance['available_balance'] < teo_amount:
                return Response({
                    'success': False,
                    'error': f'Insufficient balance. Available: {balance["available_balance"]} TEO, Required: {teo_amount} TEO'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Deduct TeoCoin for course purchase
            result = hybrid_teocoin_service.debit_user(
                user=request.user,
                amount=teo_amount,
                reason=f'Course purchase: {course_id}',
                course_id=course_id
            )
            
            if not result['success']:
                return Response({
                    'success': False,
                    'error': result.get('error', 'Failed to purchase course')
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # TODO: Integrate with course enrollment system
            # This should enroll the user in the course
            
            # Get updated balance
            new_balance_data = hybrid_teocoin_service.get_user_balance(request.user)
            
            return Response({
                'success': True,
                'type': 'teocoin_payment',
                'message': 'Course purchased successfully with TeoCoin',
                'teo_used': float(teo_amount),
                'new_balance': float(new_balance_data['available_balance']),
                'course_id': course_id
            })
            
        except Exception as e:
            logger.error(f"Error purchasing course with TeoCoin: {e}")
            return Response({
                'success': False,
                'error': 'Failed to purchase course'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class StakeTokensView(APIView):
    """Stake TeoCoin tokens (Teachers only)"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """Stake TEO tokens for commission benefits (Teachers only)"""
        try:
            # Check if user is a teacher
            if request.user.role != 'teacher':
                return Response({
                    'success': False,
                    'error': 'Only teachers can stake TeoCoin tokens'
                }, status=status.HTTP_403_FORBIDDEN)
                
            amount = request.data.get('amount')
            
            if not amount or Decimal(str(amount)) <= 0:
                return Response({
                    'success': False,
                    'error': 'Valid amount required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            result = hybrid_teocoin_service.stake_tokens(
                user=request.user,
                amount=amount
            )
            
            if result['success']:
                # Get updated teacher profile info
                tier_info = None
                if hasattr(request.user, 'teacher_profile'):
                    profile = request.user.teacher_profile
                    tier_info = {
                        'tier': profile.staking_tier,
                        'tier_name': profile.get_staking_tier_display(),
                        'commission_rate': profile.commission_rate
                    }
                
                return Response({
                    'success': True,
                    'staked_amount': amount,
                    'total_staked': result['total_staked'],
                    'available_balance': result['available_balance'],
                    'new_tier_info': tier_info
                })
            else:
                return Response(result, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            logger.error(f"Error staking tokens for user {request.user.id}: {e}")
            return Response({
                'success': False,
                'error': 'Failed to stake tokens'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class UnstakeTokensView(APIView):
    """Unstake TeoCoin tokens (Teachers only)"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """Unstake TEO tokens (Teachers only)"""
        try:
            # Check if user is a teacher
            if request.user.role != 'teacher':
                return Response({
                    'success': False,
                    'error': 'Only teachers can unstake TeoCoin tokens'
                }, status=status.HTTP_403_FORBIDDEN)
                
            amount = request.data.get('amount')
            
            if not amount or Decimal(str(amount)) <= 0:
                return Response({
                    'success': False,
                    'error': 'Valid amount required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            result = hybrid_teocoin_service.unstake_tokens(
                user=request.user,
                amount=amount
            )
            
            if result['success']:
                # Get updated teacher profile info
                tier_info = None
                if hasattr(request.user, 'teacher_profile'):
                    profile = request.user.teacher_profile
                    tier_info = {
                        'tier': profile.staking_tier,
                        'tier_name': profile.get_staking_tier_display(),
                        'commission_rate': profile.commission_rate
                    }
                
                return Response({
                    'success': True,
                    'unstaked_amount': amount,
                    'total_staked': result['total_staked'],
                    'available_balance': result['available_balance'],
                    'new_tier_info': tier_info
                })
            else:
                return Response(result, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            logger.error(f"Error unstaking tokens for user {request.user.id}: {e}")
            return Response({
                'success': False,
                'error': 'Failed to unstake tokens'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class StakingInfoView(APIView):
    """Get teacher staking information"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get teacher's staking info and tier details"""
        try:
            db_service = DBTeoCoinService()
            balance_data = db_service.get_user_balance(request.user)
            
            # Get teacher profile info if available
            tier_info = {
                'tier': 0,
                'tier_name': 'Bronze',
                'commission_rate': 50.0,
                'staked_balance': balance_data['staked_balance']
            }
            
            if hasattr(request.user, 'teacher_profile'):
                profile = request.user.teacher_profile
                tier_info.update({
                    'tier': getattr(profile, 'staking_tier_numeric', 0),
                    'tier_name': profile.get_staking_tier_display() if hasattr(profile, 'get_staking_tier_display') else 'Bronze',
                    'commission_rate': float(profile.commission_rate),
                    'staked_balance': balance_data['staked_balance']
                })
            
            return Response({
                'success': True,
                'staking_info': tier_info
            })
            
        except Exception as e:
            logger.error(f"Error getting staking info for user {request.user.id}: {e}")
            return Response({
                'success': False,
                'error': 'Failed to get staking information'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class WithdrawTokensView(APIView):
    """Create withdrawal request to MetaMask"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """Create withdrawal request and auto-process it immediately"""
        try:
            amount = request.data.get('amount')
            wallet_address = request.data.get('wallet_address')
            
            if not amount or not wallet_address:
                return Response({
                    'success': False,
                    'error': 'Amount and wallet address required'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Import services
            from services.teocoin_withdrawal_service import teocoin_withdrawal_service
            from decimal import Decimal
            
            try:
                amount_decimal = Decimal(str(amount))
            except (ValueError, TypeError):
                return Response({
                    'success': False,
                    'error': 'Invalid amount format'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Get client IP for security
            ip_address = request.META.get('HTTP_X_FORWARDED_FOR', '').split(',')[0] or request.META.get('REMOTE_ADDR')
            
            # Create withdrawal request using the enhanced service
            result = teocoin_withdrawal_service.create_withdrawal_request(
                user=request.user,
                amount=amount_decimal,
                wallet_address=wallet_address,
                ip_address=ip_address,
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            if result['success']:
                withdrawal_id = result['withdrawal_id']
                
                # 🚀 AUTO-PROCESS: Immediately mint the tokens
                logger.info(f"🎯 Auto-processing withdrawal #{withdrawal_id} for {request.user.email}")
                
                mint_result = teocoin_withdrawal_service.mint_tokens_to_address(
                    amount=amount_decimal,
                    to_address=wallet_address,
                    withdrawal_id=withdrawal_id
                )
                
                if mint_result['success']:
                    # Update withdrawal to completed
                    from blockchain.models import TeoCoinWithdrawalRequest, DBTeoCoinBalance
                    
                    withdrawal = TeoCoinWithdrawalRequest.objects.get(id=withdrawal_id)
                    withdrawal.status = 'completed'
                    withdrawal.transaction_hash = mint_result.get('transaction_hash', 'demo')
                    withdrawal.save()
                    
                    # Update user balance
                    balance_obj, created = DBTeoCoinBalance.objects.get_or_create(
                        user=request.user,
                        defaults={
                            'available_balance': Decimal('0.00'),
                            'staked_balance': Decimal('0.00'),
                            'pending_withdrawal': Decimal('0.00')
                        }
                    )
                    balance_obj.pending_withdrawal -= amount_decimal
                    balance_obj.save()
                    
                    logger.info(f"✅ Auto-processed withdrawal #{withdrawal_id} successfully")
                    
                    return Response({
                        'success': True,
                        'message': f'✅ {amount_decimal} TEO minted successfully to your MetaMask wallet!',
                        'withdrawal_id': withdrawal_id,
                        'amount': str(amount_decimal),
                        'wallet_address': wallet_address,
                        'status': 'completed',
                        'transaction_hash': mint_result.get('transaction_hash'),
                        'gas_used': mint_result.get('gas_used'),
                        'auto_processed': True
                    })
                else:
                    logger.warning(f"⚠️ Auto-processing failed for #{withdrawal_id}: {mint_result.get('error')}")
                    
                    # Return pending status as fallback
                    return Response({
                        'success': True,
                        'message': 'Withdrawal request created - processing in background',
                        'withdrawal_id': withdrawal_id,
                        'status': 'pending',
                        'auto_processed': False,
                        'note': 'Auto-processing failed, will be processed manually'
                    })
            else:
                return Response({
                    'success': False,
                    'error': result['error']
                }, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            logger.error(f"Error creating withdrawal for user {request.user.id}: {e}")
            return Response({
                'success': False,
                'error': 'Failed to create withdrawal request'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class WithdrawalStatusView(APIView):
    """Get withdrawal request status"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request, withdrawal_id):
        """Get status of specific withdrawal request"""
        try:
            withdrawal = TeoCoinWithdrawalRequest.objects.get(
                id=withdrawal_id,
                user=request.user
            )
            
            return Response({
                'success': True,
                'withdrawal': {
                    'id': withdrawal.pk,
                    'amount': str(withdrawal.amount),
                    'wallet_address': withdrawal.wallet_address,
                    'status': withdrawal.status,
                    'blockchain_tx_hash': withdrawal.blockchain_tx_hash,
                    'created_at': withdrawal.created_at.isoformat(),
                    'completed_at': withdrawal.completed_at.isoformat() if withdrawal.completed_at else None,
                    'error_message': withdrawal.error_message
                }
            })
            
        except TeoCoinWithdrawalRequest.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Withdrawal request not found'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error getting withdrawal status: {e}")
            return Response({
                'success': False,
                'error': 'Failed to get withdrawal status'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class TransactionHistoryView(APIView):
    """Get user's transaction history"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get user's TeoCoin transaction history"""
        try:
            limit = int(request.GET.get('limit', 50))
            db_service = DBTeoCoinService()
            transactions = db_service.get_user_transactions(
                user=request.user,
                limit=limit
            )
            
            return Response({
                'success': True,
                'transactions': transactions
            })
            
        except Exception as e:
            logger.error(f"Error getting transactions for user {request.user.id}: {e}")
            return Response({
                'success': False,
                'error': 'Failed to get transaction history'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class PlatformStatisticsView(APIView):
    """Get platform-wide TeoCoin statistics"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get platform TeoCoin statistics"""
        try:
            db_service = DBTeoCoinService()
            stats = db_service.get_platform_statistics()
            
            # Return basic stats for all authenticated users
            return Response({
                'success': True,
                'statistics': stats
            })
            
        except Exception as e:
            logger.error(f"Error getting platform statistics: {e}")
            return Response({
                'success': False,
                'error': 'Failed to get platform statistics'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CreditUserView(APIView):
    """Credit TEO to user (admin only)"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """Credit TEO tokens to a user"""
        try:
            # Check if user is admin/staff
            if not request.user.is_staff:
                return Response({
                    'success': False,
                    'error': 'Admin access required'
                }, status=status.HTTP_403_FORBIDDEN)
            
            user_id = request.data.get('user_id')
            amount = request.data.get('amount')
            reason = request.data.get('reason', 'Admin credit')
            
            if not user_id or not amount:
                return Response({
                    'success': False,
                    'error': 'User ID and amount required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            from django.contrib.auth import get_user_model
            User = get_user_model()
            
            target_user = User.objects.get(id=user_id)
            
            db_service = DBTeoCoinService()
            result = db_service.add_balance(
                user=target_user,
                amount=amount,
                transaction_type='admin_credit',
                description=reason
            )
            
            return Response(result)
            
        except Exception as e:
            logger.error(f"Error crediting user: {e}")
            return Response({
                'success': False,
                'error': 'Failed to credit user'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
