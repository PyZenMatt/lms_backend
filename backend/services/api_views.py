"""
Services API Views
Provides API endpoints for TeoCoin services.
After cleanup, this focuses on database-only operations.
"""

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import get_user_model

from services.hybrid_teocoin_service import hybrid_teocoin_service

User = get_user_model()


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def earnings_history(request):
    """
    Get user's TeoCoin transaction history (earnings and expenditures)
    Using the clean database system instead of the old blockchain earning service.
    """
    try:
        limit = int(request.GET.get('limit', 50))
        limit = min(limit, 200)  # Cap at 200
        
        # Get transactions from the clean database service
        transactions = hybrid_teocoin_service.get_user_transactions(
            user=request.user,
            limit=limit
        )
        
        return Response({
            'success': True,
            'transactions': transactions,
            'count': len(transactions),
            'message': 'Transaction history retrieved successfully'
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'success': False,
            'error': f'Failed to get transaction history: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
