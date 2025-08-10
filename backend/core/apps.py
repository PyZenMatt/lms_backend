"""
Core Django app configuration for the TeoArt School Platform.

This module configures the core Django application and handles initialization
of signals and cache invalidation systems when the app is ready.
"""
from django.apps import AppConfig


class CoreConfig(AppConfig):
    """
    Configuration for the Core Django application.
    
    The core app provides shared functionality across the platform including:
    - API standards and response formatting
    - Performance monitoring middleware
    - Health check systems
    - Cache management and invalidation
    - Signal handling for business logic
    - Shared serializers and utilities
    """
    
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'
    verbose_name = 'Core Platform Services'

    def ready(self):
        """
        Initialize the core app when Django starts.
        
        This method is called when the app is ready and registers
        signal handlers and cache invalidation systems.
        """
        try:
            # Import and register signal handlers
            import core.signals
            
            # Import and register cache invalidation signals
            import core.cache_signals
            
            # Import database optimizations
            import core.db_backend
            
        except ImportError as e:
            # Log import errors but don't fail app startup
            import logging
            logger = logging.getLogger('core')
            logger.warning(f"Failed to import some core modules: {e}")