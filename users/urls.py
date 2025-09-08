from django.urls import path

from .views import (
    ApproveTeacherView,
    PendingTeachersView,
    RejectTeacherView,
    UserProfileView,
    UserProgressView,
    UserSettingsView,
)
from .views.self_verify import SelfVerifyView
from .views import ConnectWalletView, DisconnectWalletView, WalletChallengeView, WalletLinkView

urlpatterns = [
    path("pending-teachers/", PendingTeachersView.as_view(), name="pending-teachers"),
    path(
        "approve-teacher/<int:user_id>/",
        ApproveTeacherView.as_view(),
        name="approve-teacher",
    ),
    path(
        "reject-teacher/<int:user_id>/",
        RejectTeacherView.as_view(),
        name="reject-teacher",
    ),
    path("profile/", UserProfileView.as_view(), name="user-profile"),
    path("profile/settings/", UserSettingsView.as_view(), name="user-settings"),
    path("profile/progress/", UserProgressView.as_view(), name="user-progress"),
    # Wallet management
    path("wallet/connect/", ConnectWalletView.as_view(), name="connect-wallet"),
    path(
        "wallet/disconnect/", DisconnectWalletView.as_view(), name="disconnect-wallet"
    ),
    path("wallet/challenge/", WalletChallengeView.as_view(), name="wallet-challenge"),
    path("wallet/link/", WalletLinkView.as_view(), name="wallet-link"),
    path("self-verify/", SelfVerifyView.as_view(), name="self-verify"),
]

# Clearer, namespaced admin-friendly aliases for teacher approval flows.
# These point to the same views but provide a predictable path under
# /api/v1/users/teachers/... which is easier for frontend wiring and docs.
urlpatterns += [
    path("teachers/pending/", PendingTeachersView.as_view(), name="pending-teachers-compat"),
    path("teachers/<int:user_id>/approve/", ApproveTeacherView.as_view(), name="approve-teacher-compat"),
    path("teachers/<int:user_id>/reject/", RejectTeacherView.as_view(), name="reject-teacher-compat"),
]

# Additional exact compatibility paths so callers that expect the extra
# "users" segment (e.g. /api/v1/users/teachers/...) will work even though
# `users.urls` is currently included at /api/v1/ in the root urls.
urlpatterns += [
    path("users/teachers/pending/", PendingTeachersView.as_view(), name="pending-teachers-compat2"),
    path("users/teachers/<int:user_id>/approve/", ApproveTeacherView.as_view(), name="approve-teacher-compat2"),
    path("users/teachers/<int:user_id>/reject/", RejectTeacherView.as_view(), name="reject-teacher-compat2"),
]
