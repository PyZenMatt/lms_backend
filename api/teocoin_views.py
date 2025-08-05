"""
TeoCoin Withdrawal API Views
Provides REST API endpoints for withdrawal functionality
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework import status
from decimal import Decimal
import logging

from services.teocoin_withdrawal_service import teocoin_withdrawal_service
from services.hybrid_teocoin_service import hybrid_teocoin_service

logger = logging.getLogger(__name__)


class GetBalanceView(APIView):
    """Get current user's TeoCoin balance"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """
        Get user's current TeoCoin balance
        
        Returns:
        {
            "success": true,
            "balance": {
                "available": "123.45",
                "staked": "250.00",
                "pending_withdrawal": "0.00",
                "total": "373.45"
            },
            "user_role": "student"
        }
        """
        try:
            # Use the db_teocoin_service to get balance
            from services.db_teocoin_service import db_teocoin_service
            result = db_teocoin_service.get_user_balance(request.user)
            
            return Response({
                'success': True,
                'balance': {
                    'available': str(result['available_balance']),
                    'staked': str(result['staked_balance']),
                    'pending_withdrawal': str(result.get('pending_withdrawal', 0)),
                    'total': str(result['total_balance'])
                },
                'user_role': request.user.role if hasattr(request.user, 'role') else 'unknown'
            })
        except Exception as e:
            logger.error(f"Error getting balance for user {request.user.id}: {str(e)}")
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CreateWithdrawalView(APIView):
    """Create a new withdrawal request"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """
        Create withdrawal request
        
        Body:
        {
            "amount": "10.50",
            "wallet_address": "0x1234567890123456789012345678901234567890"
        }
        """
        try:
            amount = request.data.get('amount')
            wallet_address = request.data.get('wallet_address')
            
            # Validation
            if not amount:
                return Response({
                    'success': False,
                    'error': 'Amount is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            if not wallet_address:
                return Response({
                    'success': False,
                    'error': 'Wallet address is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            try:
                amount_decimal = Decimal(str(amount))
                if amount_decimal <= 0:
                    return Response({
                        'success': False,
                        'error': 'Amount must be greater than 0'
                    }, status=status.HTTP_400_BAD_REQUEST)
            except (ValueError, TypeError):
                return Response({
                    'success': False,
                    'error': 'Invalid amount format'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Create withdrawal request
            result = teocoin_withdrawal_service.create_withdrawal_request(
                user=request.user,
                amount=amount_decimal,
                wallet_address=wallet_address
            )
            
            if result['success']:
                return Response({
                    'success': True,
                    'withdrawal_id': result['withdrawal_id'],
                    'amount': str(result['amount']),
                    'wallet_address': result['wallet_address'],
                    'status': result['status'],
                    'estimated_processing_time': result['estimated_processing_time'],
                    'message': result['message']
                }, status=status.HTTP_201_CREATED)
            else:
                return Response({
                    'success': False,
                    'error': result['error']
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            logger.error(f"Error creating withdrawal for user {request.user.email}: {e}")
            return Response({
                'success': False,
                'error': 'Internal server error'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


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
                    'error': result['error']
                }, status=status.HTTP_404_NOT_FOUND)
                
        except Exception as e:
            logger.error(f"Error getting withdrawal status {withdrawal_id}: {e}")
            return Response({
                'success': False,
                'error': 'Internal server error'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class UserWithdrawalHistoryView(APIView):
    """Get user's withdrawal history"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get current user's withdrawal history"""
        try:
            limit = int(request.query_params.get('limit', 20))
            limit = min(limit, 100)  # Cap at 100
            
            withdrawals = teocoin_withdrawal_service.get_user_withdrawal_history(
                user=request.user,
                limit=limit
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
                'error': 'Internal server error'
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
                    'amount_returned': str(result['amount_returned'])
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'success': False,
                    'error': result['error']
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            logger.error(f"Error cancelling withdrawal {withdrawal_id}: {e}")
            return Response({
                'success': False,
                'error': 'Internal server error'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class DBTeoCoinBalanceView(APIView):
    """Get user's DB TeoCoin balance"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get current user's TeoCoin balance"""
        try:
            balance_data = hybrid_teocoin_service.get_user_balance(request.user)
            
            return Response({
                'success': True,
                'balance': {
                    'available': str(balance_data['available_balance']),
                    'staked': str(balance_data['staked_balance']),
                    'pending_withdrawal': str(balance_data['pending_withdrawal']),
                    'total': str(balance_data['total_balance']),
                    'source': balance_data['source']
                }
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error getting balance for {request.user.email}: {e}")
            return Response({
                'success': False,
                'error': 'Internal server error'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class TeoCoinTransactionHistoryView(APIView):
    """Get user's TeoCoin transaction history"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get current user's transaction history"""
        try:
            limit = int(request.query_params.get('limit', 50))
            limit = min(limit, 200)  # Cap at 200
            
            transactions = hybrid_teocoin_service.get_user_transactions(
                user=request.user,
                limit=limit
            )
            
            return Response({
                'success': True,
                'transactions': transactions,
                'count': len(transactions)
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error getting transactions for {request.user.email}: {e}")
            return Response({
                'success': False,
                'error': 'Internal server error'
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
                'error': 'Internal server error'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AdminWithdrawalStatsView(APIView):
    """Admin view for withdrawal statistics"""
    permission_classes = [IsAdminUser]
    
    def get(self, request):
        """Get withdrawal statistics (admin only)"""
        try:
            stats = teocoin_withdrawal_service.get_withdrawal_statistics()
            
            return Response({
                'success': True,
                'statistics': stats
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error getting withdrawal statistics (admin): {e}")
            return Response({
                'success': False,
                'error': 'Internal server error'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AdminPlatformStatsView(APIView):
    """Admin view for platform TeoCoin statistics"""
    permission_classes = [IsAdminUser]
    
    def get(self, request):
        """Get platform TeoCoin statistics (admin only)"""
        try:
            stats = hybrid_teocoin_service.get_platform_statistics()
            
            return Response({
                'success': True,
                'platform_statistics': stats
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error getting platform statistics (admin): {e}")
            return Response({
                'success': False,
                'error': 'Internal server error'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
