"""
Users app modular views
"""

# User profile views (including registration)
from .user_profile_views import (
    RegisterView,
    user_profile,
    UserProfileView
)

# Teacher approval views  
from .teacher_approval_views import (
    PendingTeachersView,
    ApproveTeacherView,
    RejectTeacherView
)

# User settings and progress views
from .user_settings_views import (
    UserSettingsView,
    UserProgressView
)

# Wallet management views
from .wallet_views import (
    ConnectWalletView,
    DisconnectWalletView
)

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
