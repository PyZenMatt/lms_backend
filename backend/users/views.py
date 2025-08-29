"""
Users app views - Backward compatibility imports from modular structure
"""

# Import all views from modular structure for backward compatibility
from .views import (  # Registration; User profile; Teacher approval; Settings and progress
    ApproveTeacherView,
    PendingTeachersView,
    RegisterView,
    RejectTeacherView,
    UserProfileView,
    UserProgressView,
    UserSettingsView,
    user_profile,
)

# Re-export wallet_link views (modular views live in users/views/*.py)
try:
    from .views.wallet_link import WalletChallengeView, WalletLinkView
except Exception:
    # best-effort import; in some environments the package layout may differ
    WalletChallengeView = None  # type: ignore
    WalletLinkView = None  # type: ignore

# Re-export for backward compatibility
__all__ = [
    "RegisterView",
    "user_profile",
    "UserProfileView",
    "PendingTeachersView",
    "ApproveTeacherView",
    "RejectTeacherView",
    "UserSettingsView",
    "UserProgressView",
    # Wallet linking (re-exported)
    "WalletChallengeView",
    "WalletLinkView",
]
