"""
Services Package for TeoArt School Platform

This package contains all business logic services that handle
the core operations of the platform, separated from views.

Services:
- UserService: User management and authentication
- CourseService: Course management and enrollment
- BlockchainService: Blockchain and TeoCoin operations
- NotificationService: Email and in-app notifications
- DBTeoCoinService: Clean database-based TeoCoin operations
"""

# Default app config
default_app_config = 'services.apps.ServicesConfig'

# Services will be imported dynamically to avoid Django startup issues
__all__ = [
    'BaseService',
    'TransactionalService',
    'UserService',
    'user_service',
    'db_teocoin_service',
    'hybrid_teocoin_service',
]

def __getattr__(name):
    """Lazy import of services to avoid Django startup issues"""
    if name == 'user_service':
        from .user_service import user_service as _user_service
        return _user_service
    elif name == 'UserService':
        from .user_service import UserService
        return UserService
    elif name == 'db_teocoin_service':
        from .db_teocoin_service import db_teocoin_service
        return db_teocoin_service
    elif name == 'hybrid_teocoin_service':
        from .hybrid_teocoin_service import hybrid_teocoin_service
        return hybrid_teocoin_service
    elif name == 'BaseService':
        from .base import BaseService
        return BaseService
    elif name == 'TransactionalService':
        from .base import TransactionalService
        return TransactionalService
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
