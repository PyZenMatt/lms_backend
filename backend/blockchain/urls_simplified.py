"""
Simplified Blockchain URLs

Only essential endpoints for MetaMask integration:
- Wallet balance queries (for verification)
- Token information (for frontend display)
- Transaction receipt verification (for burn deposits)

Core TeoCoin operations use /api/v1/teocoin/ endpoints.
"""

from django.urls import path

from .views_simplified import (
    check_transaction_status,
    get_token_info,
    get_wallet_balance,
    verify_deposit,
    wallet_withdraw,
)

app_name = "blockchain"

urlpatterns = [
    # Essential blockchain queries
    path("balance/", get_wallet_balance, name="get_balance"),
    path("token-info/", get_token_info, name="token_info"),
    path("tx-status/", check_transaction_status, name="transaction_status"),
    # Verify an on-chain deposit and credit the user's DB balance
    path("deposit/verify/", verify_deposit, name="deposit_verify"),
    # Create withdrawal request and optionally auto-process via mintTo
    path("wallet/withdraw/", wallet_withdraw, name="wallet_withdraw"),
]
