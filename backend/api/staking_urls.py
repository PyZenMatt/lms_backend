"""
URL patterns for staking API endpoints
"""

from django.urls import path
from . import staking_views

urlpatterns = [
    # Staking information
    path('info/', staking_views.get_staking_info, name='get_staking_info'),
    
    # Staking operations
    path('stake/', staking_views.stake_tokens, name='stake_tokens'),
    path('unstake/', staking_views.unstake_tokens, name='unstake_tokens'),
    
    # Staking configuration
    path('tiers/', staking_views.get_staking_tiers, name='get_staking_tiers'),
    path('calculator/', staking_views.calculate_commission, name='calculate_commission'),
]
