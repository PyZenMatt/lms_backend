from django.urls import path

from .admin_views import (
    admin_retry_transaction,
    admin_transactions_list,
    admin_transactions_stats,
    admin_user_transactions,
)
from .views import TransactionHistoryView
from .views.reward_views import (
    bulk_process_rewards,
    get_reward_leaderboard,
    get_reward_summary,
    trigger_achievement_reward,
    trigger_course_completion_check,
    trigger_lesson_completion_reward,
)
from .views.discount_views import (
    preview_discount,
    confirm_discount,
    missing_snapshots_for_teachers,
    backfill_snapshots_to_decisions,
    pending_discount_snapshots,
    accept_teacher_choice,
    decline_teacher_choice,
)
from .views.teocoin_views import (
    staking_overview,
    get_staking_tiers_rewards,
    stake_from_rewards,
    unstake_from_rewards,
)
from .views.simple_transaction_views import ApplyDiscountView, TeacherDecisionView

app_name = "rewards"

urlpatterns = [
    # Alias chiamato dal FE per la cronologia del wallet
    path("wallet/transactions/", TransactionHistoryView.as_view(), name="wallet-transactions"),
    # Blockchain transaction endpoints
    path("transactions/", TransactionHistoryView.as_view(), name="transaction-history"),
    # Admin endpoints
    path("admin/transactions/", admin_transactions_list, name="admin-transactions"),
    path(
        "admin/transactions/stats/",
        admin_transactions_stats,
        name="admin-transactions-stats",
    ),
    path(
        "admin/transactions/<int:transaction_id>/retry/",
        admin_retry_transaction,
        name="admin-retry-transaction",
    ),
    path(
        "admin/users/<int:user_id>/transactions/",
        admin_user_transactions,
        name="admin-user-transactions",
    ),
    # RewardService-based endpoints (new)
    path(
        "rewards/complete-lesson/",
        trigger_lesson_completion_reward,
        name="complete-lesson",
    ),
    path(
        "rewards/course-completion/",
        trigger_course_completion_check,
        name="course-completion-reward",
    ),
    path("rewards/user-summary/", get_reward_summary, name="user-rewards-summary"),
    path("rewards/leaderboard/", get_reward_leaderboard, name="reward-leaderboard"),
    # Legacy endpoints (backward compatibility)
    path(
        "rewards/lesson-completion/",
        trigger_lesson_completion_reward,
        name="lesson-completion-reward",
    ),
    path("rewards/achievement/", trigger_achievement_reward, name="achievement-reward"),
    path("rewards/summary/", get_reward_summary, name="reward-summary"),
    path("rewards/bulk/", bulk_process_rewards, name="bulk-reward"),
    # Discount preview/confirm endpoints
    path("rewards/discounts/preview/", preview_discount, name="discount-preview"),
    path("rewards/discounts/confirm/", confirm_discount, name="discount-confirm"),
    path("rewards/discounts/pending/", pending_discount_snapshots, name="discount-pending"),
    # Backfill: list snapshots that probably missed teacher notifications
    path("rewards/discounts/missing-for-teacher/", missing_snapshots_for_teachers, name="discount-missing-for-teacher"),
    path("rewards/discounts/backfill/", backfill_snapshots_to_decisions, name="discount-backfill"),
    # Minimal KISS transaction endpoints
    path("rewards/discounts/apply/", ApplyDiscountView.as_view(), name="apply-discount"),
    path("rewards/teacher-decisions/<int:decision_id>/<str:action>/", TeacherDecisionView.as_view(), name="teacher-decision"),
    # Compat: endpoints chiamati dal FE per accettare/declinare i TEO (KISS)
    path("rewards/discounts/<int:decision_id>/accept/", accept_teacher_choice, name="discount-accept"),
    path("rewards/discounts/<int:decision_id>/decline/", decline_teacher_choice, name="discount-decline"),
    # Backwards compat for older FE (also kept)
    path("teacher-choices/<int:decision_id>/accept/", accept_teacher_choice, name="teacher-choice-accept"),
    # Compatibility staking endpoints used by frontend wrappers
    # Backwards-compatible staking overview used by frontend
    path("rewards/staking/overview/", staking_overview, name="staking-overview"),
    path("rewards/staking/tiers/", get_staking_tiers_rewards, name="staking-tiers"),
    path("rewards/staking/stake/", stake_from_rewards, name="staking-stake"),
    path("rewards/staking/unstake/", unstake_from_rewards, name="staking-unstake"),
]
