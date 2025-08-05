"""
Wallet management views for user profiles
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.utils import timezone


class ConnectWalletView(APIView):
    """Connect a wallet to user profile"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Connect wallet address to user profile"""
        try:
            wallet_address = request.data.get('wallet_address')
            
            if not wallet_address:
                return Response(
                    {'error': 'Wallet address is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Validate wallet address format (basic check)
            if not wallet_address.startswith('0x') or len(wallet_address) != 42:
                return Response(
                    {'error': 'Invalid wallet address format'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Update user's wallet address
            user = request.user
            user.wallet_address = wallet_address
            user.save()
            
            return Response({
                'success': True,
                'message': 'Wallet connected successfully',
                'wallet_address': wallet_address,
                'user_id': user.id
            })
            
        except Exception as e:
            return Response(
                {'error': f'Error connecting wallet: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class DisconnectWalletView(APIView):
    """Disconnect wallet from user profile"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Disconnect wallet address from user profile"""
        try:
            user = request.user
            
            if not user.wallet_address:
                return Response(
                    {'error': 'No wallet connected to this account'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Store old address for response
            old_address = user.wallet_address
            
            # Remove wallet address
            user.wallet_address = None
            user.save()
            
            return Response({
                'success': True,
                'message': 'Wallet disconnected successfully',
                'previous_address': old_address,
                'user_id': user.id
            })
            
        except Exception as e:
            return Response(
                {'error': f'Error disconnecting wallet: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
