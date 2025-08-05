from rest_framework import generics, filters as drf_filters
from rest_framework.permissions import IsAuthenticated
from ..serializers import BlockchainTransactionSerializer
from ..models import BlockchainTransaction


class TransactionHistoryView(generics.ListAPIView):
    """List view for user's blockchain transaction history with filtering"""
    serializer_class = BlockchainTransactionSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [drf_filters.SearchFilter, drf_filters.OrderingFilter]
    search_fields = ['transaction_type']
    ordering_fields = ['created_at', 'amount']
    ordering = ['-created_at']  # Default ordering

    def get_queryset(self):  # type: ignore
        """Filter transactions by authenticated user and optional date range"""
        user = self.request.user
        queryset = BlockchainTransaction.objects.filter(user=user)
        
        # Handle date filtering safely for both DRF and regular Django requests
        query_params = getattr(self.request, 'query_params', getattr(self.request, 'GET', {}))
        date_from = query_params.get('from')
        date_to = query_params.get('to')
        
        if date_from:
            queryset = queryset.filter(created_at__gte=date_from)
        if date_to:
            queryset = queryset.filter(created_at__lte=date_to)
            
        return queryset
