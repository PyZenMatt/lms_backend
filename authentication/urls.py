"""
URL configuration for the authentication app.

This module defines all the URL patterns for authentication-related views:
- User registration
- Email verification
- Login/logout (both API and template views)
- JWT token management (obtain and refresh)
"""

from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView
from .views import CustomTokenRefreshView

from .views import LoginApiView, LogoutView, RegisterView, VerifyEmailView

urlpatterns = [
    # User registration endpoint
    path("register/", RegisterView.as_view(), name="register"),
    # Compatibility alias for older frontend clients that call token/register/
    path("token/register/", RegisterView.as_view(), name="token-register-alias"),
    # Email verification endpoint (GET request with UID and token)
    path(
        "verify-email/<str:uid>/<str:token>/",
        VerifyEmailView.as_view(),
        name="verify-email",
    ),
    # API login endpoint (returns JWT tokens)
    path("login/", LoginApiView.as_view(), name="api-login"),
    # API logout endpoint (blacklists refresh token)
    path("logout/", LogoutView.as_view(), name="logout"),
    # JWT token endpoints
    path(
        "token/", TokenObtainPairView.as_view(), name="token_obtain_pair"
    ),  # Get access/refresh tokens
    path(
        "token/refresh/", CustomTokenRefreshView.as_view(), name="token_refresh"
    ),  # Refresh access token (customized to include role claim)
]
