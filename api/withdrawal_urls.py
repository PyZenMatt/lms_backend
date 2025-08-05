"""
URL patterns for TeoCoin withdrawal API endpoints
Following RESTful API design principles
"""

from django.urls import path
from . import withdrawal_views

app_name = 'withdrawal'

urlpatterns = [
    # User withdrawal endpoints
    path('create/', withdrawal_views.CreateWithdrawalView.as_view(), name='create_withdrawal'),
    path('<int:withdrawal_id>/status/', withdrawal_views.WithdrawalStatusView.as_view(), name='withdrawal_status'),
    path('<int:withdrawal_id>/cancel/', withdrawal_views.CancelWithdrawalView.as_view(), name='cancel_withdrawal'),
    path('<int:withdrawal_id>/process/', withdrawal_views.ProcessWithdrawalView.as_view(), name='process_withdrawal'),
    path('pending/', withdrawal_views.UserPendingWithdrawalsView.as_view(), name='user_pending'),
    path('history/', withdrawal_views.UserWithdrawalHistoryView.as_view(), name='withdrawal_history'),
    path('balance/', withdrawal_views.UserTeoCoinBalanceView.as_view(), name='user_balance'),
    path('limits/', withdrawal_views.WithdrawalLimitsView.as_view(), name='withdrawal_limits'),
    
    # Admin endpoints
    path('admin/pending/', withdrawal_views.AdminPendingWithdrawalsView.as_view(), name='admin_pending'),
    path('admin/stats/', withdrawal_views.AdminWithdrawalStatsView.as_view(), name='admin_stats'),
]
