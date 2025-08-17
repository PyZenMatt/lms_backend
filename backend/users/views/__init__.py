"""
Users app modular views
"""

# Teacher approval views
from .teacher_approval_views import (ApproveTeacherView, PendingTeachersView,
                                     RejectTeacherView)
# User profile views (including registration)
from .user_profile_views import RegisterView, UserProfileView, user_profile
# User settings and progress views
from .user_settings_views import UserProgressView, UserSettingsView
# Wallet management views
from .wallet_views import ConnectWalletView, DisconnectWalletView

__all__ = [
    # Registration
    'RegisterView',

    # User profile
    'user_profile',
    'UserProfileView',

    # Teacher approval
    'PendingTeachersView',
    'ApproveTeacherView',
    'RejectTeacherView',

    # Settings and progress
    'UserSettingsView',
    'UserProgressView',

    # Wallet management
    'ConnectWalletView',
    'DisconnectWalletView',
]
