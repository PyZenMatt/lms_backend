from django.urls import path
from .views import (
    TransactionHistoryView,
)
from .views.reward_views import (
    trigger_lesson_completion_reward,
    trigger_course_completion_check,
    trigger_achievement_reward,
    get_reward_summary,
    get_reward_leaderboard,
    bulk_process_rewards
)
from .admin_views import (
    admin_transactions_list,
    admin_transactions_stats,
    admin_retry_transaction,
    admin_user_transactions
)

app_name = 'rewards'

urlpatterns = [
    # Blockchain transaction endpoints
    path('transactions/', TransactionHistoryView.as_view(), name='transaction-history'),
    
    # Admin endpoints
    path('admin/transactions/', admin_transactions_list, name='admin-transactions'),
    path('admin/transactions/stats/', admin_transactions_stats, name='admin-transactions-stats'),
    path('admin/transactions/<int:transaction_id>/retry/', admin_retry_transaction, name='admin-retry-transaction'),
    path('admin/users/<int:user_id>/transactions/', admin_user_transactions, name='admin-user-transactions'),
    
    # RewardService-based endpoints (new)
    path('rewards/complete-lesson/', trigger_lesson_completion_reward, name='complete-lesson'),
    path('rewards/course-completion/', trigger_course_completion_check, name='course-completion-reward'),
    path('rewards/user-summary/', get_reward_summary, name='user-rewards-summary'),
    path('rewards/leaderboard/', get_reward_leaderboard, name='reward-leaderboard'),
    
    # Legacy endpoints (backward compatibility)
    path('rewards/lesson-completion/', trigger_lesson_completion_reward, name='lesson-completion-reward'),
    path('rewards/achievement/', trigger_achievement_reward, name='achievement-reward'),
    path('rewards/summary/', get_reward_summary, name='reward-summary'),
    path('rewards/bulk/', bulk_process_rewards, name='bulk-reward'),
]