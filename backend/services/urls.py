"""
URL patterns for services app including TEO earning and TeoCoin discount endpoints
"""

from django.urls import path, include
from . import api_views

urlpatterns = [
    # TEO Earning endpoints
    path('earnings/history/', api_views.earnings_history, name='earnings_history'),
    
    # TeoCoin Discount endpoints
    path('discount/', include('api.discount_urls')),
    
    # Staking endpoints
    path('staking/', include('api.staking_urls')),
]
