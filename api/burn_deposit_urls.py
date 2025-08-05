"""
URL patterns for TeoCoin Burn Deposit API endpoints
"""

from django.urls import path
from . import burn_deposit_views

app_name = 'burn_deposit'

urlpatterns = [
    # Burn deposit endpoints
    path('burn-deposit/', burn_deposit_views.BurnDepositView.as_view(), name='burn_deposit'),
    path('burn-deposit/status/<str:tx_hash>/', burn_deposit_views.BurnDepositStatusView.as_view(), name='burn_deposit_status'),
]
