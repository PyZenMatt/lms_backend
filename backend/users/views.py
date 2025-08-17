"""
Users app views - Backward compatibility imports from modular structure
"""

# Import all views from modular structure for backward compatibility
from .views import (  # Registration; User profile; Teacher approval; Settings and progress
    ApproveTeacherView, PendingTeachersView, RegisterView, RejectTeacherView,
    UserProfileView, UserProgressView, UserSettingsView, user_profile)

# Re-export for backward compatibility
__all__ = [
    'RegisterView',
    'user_profile',
    'UserProfileView',
    'PendingTeachersView',
    'ApproveTeacherView',
    'RejectTeacherView',
    'UserSettingsView',
    'UserProgressView',
]
