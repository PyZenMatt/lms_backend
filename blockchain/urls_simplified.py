"""
Simplified Blockchain URLs

Only essential endpoints for MetaMask integration:
- Wallet balance queries (for verification)
- Token information (for frontend display)
- Transaction receipt verification (for burn deposits)

Core TeoCoin operations use /api/v1/teocoin/ endpoints.
"""

from django.urls import path
from .views import (
    get_wallet_balance,
    get_token_info,
    check_transaction_status
)

app_name = 'blockchain'

urlpatterns = [
    # Essential blockchain queries
    path('balance/', get_wallet_balance, name='get_balance'),
    path('token-info/', get_token_info, name='token_info'),
    path('tx-status/', check_transaction_status, name='transaction_status'),
]
