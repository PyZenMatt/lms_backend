"""
TeoCoin API URL Configuration - Enhanced with Phase 1 Withdrawal System
"""

from django.urls import path, include
from .teocoin_views import (
    GetBalanceView,
    CreateWithdrawalView,
    WithdrawalStatusView,
    UserWithdrawalHistoryView,
    CancelWithdrawalView,
    DBTeoCoinBalanceView,
    TeoCoinTransactionHistoryView,
    AdminPendingWithdrawalsView,
    AdminWithdrawalStatsView,
    AdminPlatformStatsView
)
from .db_teocoin_views import (
    TeoCoinBalanceView,
    CalculateDiscountView,
    ApplyDiscountView,
    PurchaseCourseView,
    WithdrawTokensView,
    WithdrawalStatusView as DBWithdrawalStatusView,
    TransactionHistoryView,
    PlatformStatisticsView,
    CreditUserView
)
from .teacher_absorption_views import (
    TeacherPendingAbsorptionsView,
    TeacherMakeAbsorptionChoiceView,
    TeacherAbsorptionHistoryView,
    AdminAbsorptionOverviewView
)

app_name = 'teocoin_api'

urlpatterns = [
    # User Balance & Transactions (DB-based)
    path('student/balance/', GetBalanceView.as_view(), name='student_balance'),
    path('balance/', TeoCoinBalanceView.as_view(), name='balance'),
    path('transactions/', TransactionHistoryView.as_view(), name='transactions'),
    
    # Discount System
    path('calculate-discount/', CalculateDiscountView.as_view(), name='calculate_discount'),
    path('apply-discount/', ApplyDiscountView.as_view(), name='apply_discount'),
    path('purchase-course/', PurchaseCourseView.as_view(), name='purchase_course'),
    
    # Enhanced Withdrawal System - Phase 1 (MetaMask Integration)
    path('withdrawals/', include('api.withdrawal_urls', namespace='withdrawals')),
    
    # Burn Deposit System - Phase 2 (MetaMask → Platform)
    path('', include('api.burn_deposit_urls', namespace='burn_deposit')),
    
    # Legacy Withdrawal Management (DB-based)
    path('withdraw/', WithdrawTokensView.as_view(), name='withdraw'),
    path('withdrawal/<int:withdrawal_id>/', DBWithdrawalStatusView.as_view(), name='withdrawal_status'),
    
    # Admin & Platform
    path('statistics/', PlatformStatisticsView.as_view(), name='statistics'),
    path('credit/', CreditUserView.as_view(), name='credit'),
    
    # Teacher Discount Absorption System
    path('teacher/absorptions/', TeacherPendingAbsorptionsView.as_view(), name='teacher_pending_absorptions'),
    path('teacher/absorptions/pending/', TeacherPendingAbsorptionsView.as_view(), name='teacher_pending_absorptions_alt'),
    path('teacher/absorptions/choose/', TeacherMakeAbsorptionChoiceView.as_view(), name='teacher_make_absorption_choice'),
    path('teacher/choice/', TeacherMakeAbsorptionChoiceView.as_view(), name='teacher_choice_shortcut'),
    path('teacher/absorptions/history/', TeacherAbsorptionHistoryView.as_view(), name='teacher_absorption_history'),
    
    # Legacy endpoints (for backward compatibility)
    path('legacy/withdraw/', CreateWithdrawalView.as_view(), name='legacy_create_withdrawal'),
    path('legacy/withdraw/<int:withdrawal_id>/cancel/', CancelWithdrawalView.as_view(), name='legacy_cancel_withdrawal'),
    path('legacy/withdrawals/', UserWithdrawalHistoryView.as_view(), name='legacy_withdrawal_history'),
    path('legacy/balance/', DBTeoCoinBalanceView.as_view(), name='legacy_balance'),
    path('legacy/transactions/', TeoCoinTransactionHistoryView.as_view(), name='legacy_transactions'),
    
    # Admin Endpoints
    path('admin/withdrawals/pending/', AdminPendingWithdrawalsView.as_view(), name='admin_pending_withdrawals'),
    path('admin/withdrawals/stats/', AdminWithdrawalStatsView.as_view(), name='admin_withdrawal_stats'),
    path('admin/platform/stats/', AdminPlatformStatsView.as_view(), name='admin_platform_stats'),
    path('admin/absorptions/overview/', AdminAbsorptionOverviewView.as_view(), name='admin_absorption_overview'),
]
