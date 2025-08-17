from django.apps import AppConfig


class AuthenticationConfig(AppConfig):
    """
    Django app configuration for the authentication module.
    
    This app handles user authentication, registration, email verification,
    and JWT token management for the school platform.
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'authentication'
