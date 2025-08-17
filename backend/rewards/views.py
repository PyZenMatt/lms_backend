"""
Rewards Views Module

This module provides backward compatibility by importing all views
from the modular views structure. This allows existing imports to
continue working while providing better code organization.
"""

# Import all views from the modular structure
from .views import *

# This ensures that all existing imports like:
# from rewards.views import UserTeoCoinsView
# continue to work without any changes to other files.




