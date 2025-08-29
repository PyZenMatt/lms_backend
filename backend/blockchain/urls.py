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
    onchain_mint,
)
from .views import withdraw_to_wallet, tx_status

app_name = "blockchain"

urlpatterns = [
    # Essential blockchain queries
    path("balance/", get_wallet_balance, name="get_balance"),
    path("token-info/", get_token_info, name="token_info"),
    path("tx-status/", check_transaction_status, name="transaction_status"),
    path("onchain/mint/", onchain_mint, name="onchain_mint"),
    # idempotent withdraw for linked users
    path("wallet/withdraw/", withdraw_to_wallet, name="wallet_withdraw"),
    path("wallet/tx-status/<str:tx_identifier>/", tx_status, name="wallet_tx_status"),
    path("deposit/verify/", verify_deposit, name="deposit_verify"),
]
