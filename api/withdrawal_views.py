"""
TeoCoin Withdrawal API Views - Phase 1 Implementation
Provides REST API endpoints for withdrawal functionality following GitHub best practices

This module implements the withdrawal API endpoints as outlined in the
TeoCoin MetaMask Integration specification.
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework import status
from decimal import Decimal
import logging

from services.teocoin_withdrawal_service import teocoin_withdrawal_service
from services.db_teocoin_service import db_teocoin_service

logger = logging.getLogger(__name__)


class CreateWithdrawalView(APIView):
    """Create a new withdrawal request"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """
        Create withdrawal request
        
        Body:
        {
            "amount": "50.00",
            "metamask_address": "0x742d35Cc6475C1C2C6b2FF4a4F5D6f865c123456"
        }
        """
        try:
            amount = request.data.get('amount')
            metamask_address = request.data.get('metamask_address')
            
            # Validation
            if not amount:
                return Response({
                    'success': False,
                    'error': 'Amount is required',
                    'error_code': 'MISSING_AMOUNT'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            if not metamask_address:
                return Response({
                    'success': False,
                    'error': 'MetaMask address is required',
                    'error_code': 'MISSING_ADDRESS'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            try:
                amount_decimal = Decimal(str(amount))
                if amount_decimal <= 0:
                    return Response({
                        'success': False,
                        'error': 'Amount must be greater than 0',
                        'error_code': 'INVALID_AMOUNT'
                    }, status=status.HTTP_400_BAD_REQUEST)
            except (ValueError, TypeError):
                return Response({
                    'success': False,
                    'error': 'Invalid amount format',
                    'error_code': 'INVALID_AMOUNT_FORMAT'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Get client IP and user agent for security
            ip_address = self.get_client_ip(request)
            user_agent = request.META.get('HTTP_USER_AGENT', '')
            
            # Create withdrawal request
            result = teocoin_withdrawal_service.create_withdrawal_request(
                user=request.user,
                amount=amount_decimal,
                wallet_address=metamask_address,
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            if result['success']:
                withdrawal_id = result['withdrawal_id']
                
                # 🚀 NEW: Automatically process the withdrawal immediately
                logger.info(f"🎯 Auto-processing withdrawal #{withdrawal_id} for {request.user.email}")
                
                # Process the withdrawal with real minting
                mint_result = teocoin_withdrawal_service.mint_tokens_to_address(
                    amount=amount_decimal,
                    to_address=metamask_address,
                    withdrawal_id=withdrawal_id
                )
                
                if mint_result['success']:
                    # Update withdrawal status to completed
                    from blockchain.models import TeoCoinWithdrawalRequest, DBTeoCoinBalance
                    
                    try:
                        withdrawal = TeoCoinWithdrawalRequest.objects.get(id=withdrawal_id)
                        withdrawal.status = 'completed'
                        withdrawal.transaction_hash = mint_result.get('transaction_hash', 'pending')
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
                            'withdrawal_id': withdrawal_id,
                            'amount': str(amount_decimal),
                            'metamask_address': metamask_address,
                            'status': 'completed',
                            'transaction_hash': mint_result.get('transaction_hash'),
                            'gas_used': mint_result.get('gas_used'),
                            'message': f'✅ {amount_decimal} TEO minted successfully to your MetaMask wallet!',
                            'auto_processed': True
                        }, status=status.HTTP_201_CREATED)
                        
                    except Exception as e:
                        logger.error(f"Error updating withdrawal #{withdrawal_id} status: {e}")
                        # Return original pending response if status update fails
                        pass
                
                else:
                    logger.error(f"❌ Auto-processing failed for withdrawal #{withdrawal_id}: {mint_result.get('error')}")
                    # Return the original pending withdrawal response
                    pass
                
                # Fallback: Return original response if auto-processing fails
                return Response({
                    'success': True,
                    'withdrawal_id': result['withdrawal_id'],
                    'amount': result['amount'],
                    'metamask_address': result['metamask_address'],
                    'status': result['status'],
                    'estimated_processing_time': result['estimated_processing_time'],
                    'daily_withdrawal_count': result['daily_withdrawal_count'],
                    'message': result['message'],
                    'note': 'Auto-processing failed, withdrawal is pending manual processing'
                }, status=status.HTTP_201_CREATED)
            else:
                return Response({
                    'success': False,
                    'error': result['error'],
                    'error_code': result.get('error_code', 'UNKNOWN_ERROR')
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            logger.error(f"Error creating withdrawal for user {request.user.email}: {e}")
            return Response({
                'success': False,
                'error': 'Internal server error',
                'error_code': 'INTERNAL_ERROR'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def get_client_ip(self, request):
        """Get client IP address from request"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0]
        else:
            return request.META.get('REMOTE_ADDR')


class WithdrawalStatusView(APIView):
    """Get status of a withdrawal request"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request, withdrawal_id):
        """Get withdrawal status by ID"""
        try:
            result = teocoin_withdrawal_service.get_withdrawal_status(
                withdrawal_id=withdrawal_id,
                user=request.user
            )
            
            if result['success']:
                return Response({
                    'success': True,
                    'withdrawal': result['withdrawal']
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'success': False,
                    'error': result['error'],
                    'error_code': result.get('error_code', 'UNKNOWN_ERROR')
                }, status=status.HTTP_404_NOT_FOUND)
                
        except Exception as e:
            logger.error(f"Error getting withdrawal status {withdrawal_id}: {e}")
            return Response({
                'success': False,
                'error': 'Internal server error',
                'error_code': 'INTERNAL_ERROR'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class UserWithdrawalHistoryView(APIView):
    """Get user's withdrawal history"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get current user's withdrawal history"""
        try:
            limit = int(request.query_params.get('limit', 20))
            limit = min(limit, 100)  # Cap at 100
            
            status_filter = request.query_params.get('status')
            
            withdrawals = teocoin_withdrawal_service.get_user_withwithdrawal_history(
                user=request.user,
                limit=limit,
                status=status_filter
            )
            
            return Response({
                'success': True,
                'withdrawals': withdrawals,
                'count': len(withdrawals)
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error getting withdrawal history for {request.user.email}: {e}")
            return Response({
                'success': False,
                'error': 'Internal server error',
                'error_code': 'INTERNAL_ERROR'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CancelWithdrawalView(APIView):
    """Cancel a pending withdrawal request"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request, withdrawal_id):
        """Cancel withdrawal request"""
        try:
            result = teocoin_withdrawal_service.cancel_withdrawal_request(
                withdrawal_id=withdrawal_id,
                user=request.user
            )
            
            if result['success']:
                return Response({
                    'success': True,
                    'message': result['message'],
                    'amount_returned': result['amount_returned']
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'success': False,
                    'error': result['error'],
                    'error_code': result.get('error_code', 'UNKNOWN_ERROR')
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            logger.error(f"Error cancelling withdrawal {withdrawal_id}: {e}")
            return Response({
                'success': False,
                'error': 'Internal server error',
                'error_code': 'INTERNAL_ERROR'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class UserTeoCoinBalanceView(APIView):
    """Get user's TeoCoin balance"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get current user's TeoCoin balance"""
        try:
            balance_data = db_teocoin_service.get_user_balance(request.user)
            
            return Response({
                'success': True,
                'balance': {
                    'available': str(balance_data['available_balance']),
                    'staked': str(balance_data['staked_balance']),
                    'pending_withdrawal': str(balance_data['pending_withdrawal']),
                    'total': str(balance_data['total_balance'])
                }
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error getting balance for {request.user.email}: {e}")
            return Response({
                'success': False,
                'error': 'Internal server error',
                'error_code': 'INTERNAL_ERROR'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class WithdrawalLimitsView(APIView):
    """Get withdrawal limits and requirements"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get withdrawal limits for current user"""
        try:
            from datetime import date
            from blockchain.models import TeoCoinWithdrawalRequest
            
            # Get daily usage
            today = date.today()
            daily_withdrawals = TeoCoinWithdrawalRequest.objects.filter(
                user=request.user,
                created_at__date=today
            )
            
            daily_count = daily_withdrawals.count()
            daily_amount = sum(w.amount for w in daily_withdrawals)
            
            # Get limits from service
            limits = {
                'min_amount': str(teocoin_withdrawal_service.MIN_WITHDRAWAL_AMOUNT),
                'max_amount': str(teocoin_withdrawal_service.MAX_WITHDRAWAL_AMOUNT),
                'max_daily_withdrawals': teocoin_withdrawal_service.MAX_DAILY_WITHDRAWALS,
                'max_daily_amount': str(teocoin_withdrawal_service.MAX_DAILY_AMOUNT),
                'daily_usage': {
                    'withdrawals_used': daily_count,
                    'amount_used': str(daily_amount),
                    'withdrawals_remaining': max(0, teocoin_withdrawal_service.MAX_DAILY_WITHDRAWALS - daily_count),
                    'amount_remaining': str(max(0, teocoin_withdrawal_service.MAX_DAILY_AMOUNT - daily_amount))
                }
            }
            
            return Response({
                'success': True,
                'limits': limits
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error getting withdrawal limits for {request.user.email}: {e}")
            return Response({
                'success': False,
                'error': 'Internal server error',
                'error_code': 'INTERNAL_ERROR'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ========== ADMIN VIEWS ==========

class AdminPendingWithdrawalsView(APIView):
    """Admin view for pending withdrawals"""
    permission_classes = [IsAdminUser]
    
    def get(self, request):
        """Get all pending withdrawal requests (admin only)"""
        try:
            limit = int(request.query_params.get('limit', 50))
            limit = min(limit, 200)  # Cap at 200
            
            pending_withdrawals = teocoin_withdrawal_service.get_pending_withdrawals(limit)
            
            return Response({
                'success': True,
                'pending_withdrawals': pending_withdrawals,
                'count': len(pending_withdrawals)
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error getting pending withdrawals (admin): {e}")
            return Response({
                'success': False,
                'error': 'Internal server error',
                'error_code': 'INTERNAL_ERROR'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AdminWithdrawalStatsView(APIView):
    """Admin view for withdrawal statistics"""
    permission_classes = [IsAdminUser]
    
    def get(self, request):
        """Get withdrawal statistics (admin only)"""
        try:
            days = int(request.query_params.get('days', 30))
            days = min(days, 365)  # Cap at 1 year
            
            stats = teocoin_withdrawal_service.get_withdrawal_statistics(days)
            
            return Response({
                'success': True,
                'statistics': stats
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error getting withdrawal statistics (admin): {e}")
            return Response({
                'success': False,
                'error': 'Internal server error',
                'error_code': 'INTERNAL_ERROR'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ProcessWithdrawalView(APIView):
    """Process a specific withdrawal request - Convert pending to actual minting"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request, withdrawal_id):
        """
        Process a specific withdrawal by ID
        
        URL: /api/v1/teocoin/withdrawals/{withdrawal_id}/process/
        Body: {} (empty)
        
        Returns real-time transaction feedback including transaction hash
        """
        try:
            # Import here to avoid circular imports
            from blockchain.models import TeoCoinWithdrawalRequest
            
            # Get withdrawal request
            try:
                withdrawal = TeoCoinWithdrawalRequest.objects.get(
                    id=withdrawal_id,
                    user=request.user,
                    status='pending'
                )
            except TeoCoinWithdrawalRequest.DoesNotExist:
                return Response({
                    'success': False,
                    'error': 'Withdrawal not found or already processed',
                    'error_code': 'WITHDRAWAL_NOT_FOUND'
                }, status=status.HTTP_404_NOT_FOUND)
            
            logger.info(f"🎯 Processing withdrawal #{withdrawal_id} for user {request.user.email}")
            
            # Process the withdrawal with real minting
            result = teocoin_withdrawal_service.mint_tokens_to_address(
                amount=withdrawal.amount,
                to_address=withdrawal.metamask_address,
                withdrawal_id=withdrawal.id
            )
            
            if result['success']:
                # Update withdrawal status
                withdrawal.status = 'completed'
                withdrawal.transaction_hash = result.get('transaction_hash', 'pending')
                withdrawal.save()
                
                # Update user balance
                from blockchain.models import DBTeoCoinBalance
                balance_obj, created = DBTeoCoinBalance.objects.get_or_create(
                    user=request.user,
                    defaults={
                        'available_balance': Decimal('0.00'),
                        'staked_balance': Decimal('0.00'),
                        'pending_withdrawal': Decimal('0.00')
                    }
                )
                balance_obj.pending_withdrawal -= withdrawal.amount
                balance_obj.save()
                
                logger.info(f"✅ Withdrawal #{withdrawal_id} processed successfully")
                
                return Response({
                    'success': True,
                    'message': f'Successfully minted {withdrawal.amount} TEO to your MetaMask wallet',
                    'transaction_hash': result.get('transaction_hash'),
                    'gas_used': result.get('gas_used'),
                    'amount_minted': str(withdrawal.amount),
                    'to_address': withdrawal.metamask_address,
                    'withdrawal_id': withdrawal.id,
                    'status': 'completed'
                }, status=status.HTTP_200_OK)
            else:
                logger.error(f"❌ Withdrawal #{withdrawal_id} failed: {result.get('error')}")
                
                return Response({
                    'success': False,
                    'error': result.get('error', 'Minting failed'),
                    'error_code': 'MINTING_FAILED',
                    'withdrawal_id': withdrawal.id
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            logger.error(f"Error processing withdrawal #{withdrawal_id}: {e}")
            return Response({
                'success': False,
                'error': 'Internal server error during withdrawal processing',
                'error_code': 'INTERNAL_ERROR'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class UserPendingWithdrawalsView(APIView):
    """Get user's pending withdrawals that can be processed"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get current user's pending withdrawals"""
        try:
            from blockchain.models import TeoCoinWithdrawalRequest
            
            pending_withdrawals = TeoCoinWithdrawalRequest.objects.filter(
                user=request.user,
                status='pending'
            ).order_by('-created_at')
            
            withdrawals_data = []
            for w in pending_withdrawals:
                withdrawals_data.append({
                    'id': w.id,
                    'amount': str(w.amount),
                    'metamask_address': w.metamask_address,
                    'created_at': w.created_at.isoformat(),
                    'status': w.status,
                    'can_process': True  # User can trigger processing
                })
            
            return Response({
                'success': True,
                'pending_withdrawals': withdrawals_data,
                'count': len(withdrawals_data)
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error getting user pending withdrawals: {e}")
            return Response({
                'success': False,
                'error': 'Internal server error',
                'error_code': 'INTERNAL_ERROR'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
