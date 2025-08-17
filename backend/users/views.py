"""
Users app views - Backward compatibility imports from modular structure
"""

# Import all views from modular structure for backward compatibility
from .views import (
    # Registration
    RegisterView,
    
    # User profile
    user_profile,
    UserProfileView,
    
    # Teacher approval
    PendingTeachersView, 
    ApproveTeacherView,
    RejectTeacherView,
    
    # Settings and progress
    UserSettingsView,
    UserProgressView,
)

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