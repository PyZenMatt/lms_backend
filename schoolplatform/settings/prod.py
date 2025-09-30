import os
import re

import dj_database_url
import sentry_sdk
from sentry_sdk.integrations.celery import CeleryIntegration
from sentry_sdk.integrations.django import DjangoIntegration
from django.core.exceptions import ImproperlyConfigured  # <— mancava

from .base import *

# Ensure runtime marks this as production for settings relying on ENVIRONMENT
ENVIRONMENT = "production"

DEBUG = False

# Parse ALLOWED_HOSTS e CSRF_TRUSTED_ORIGINS
ALLOWED_HOSTS = [h.strip() for h in os.getenv("ALLOWED_HOSTS", "").split(",") if h.strip()]

# If no ALLOWED_HOSTS in env, add default ones
if not ALLOWED_HOSTS:
    ALLOWED_HOSTS = [
        "lms-api-9tns.onrender.com",  # Backend domain
        "corsi.openpython.it",        # Frontend domain (se necessario)
    ]

_raw_csrf = [h.strip() for h in os.getenv("CSRF_TRUSTED_ORIGINS", "").split(",") if h.strip()]
CSRF_TRUSTED_ORIGINS = []
for origin in _raw_csrf:
    if not re.match(r"^https?://", origin):
        raise ImproperlyConfigured(
            f"CSRF_TRUSTED_ORIGINS must start with http:// or https:// (got: '{origin}')"
        )
    CSRF_TRUSTED_ORIGINS.append(origin)

# Always ensure our required domains are included
required_origins = [
    "https://corsi.openpython.it",       # Frontend
    "https://lms-api-9tns.onrender.com", # Backend (for admin panel)
]
for origin in required_origins:
    if origin not in CSRF_TRUSTED_ORIGINS:
        CSRF_TRUSTED_ORIGINS.append(origin)

# Allow disabling SSL requirement locally by setting DB_SSL_REQUIRE=0
ssl_require = os.getenv("DB_SSL_REQUIRE", "1") not in ("0", "false", "False", "no", "No")
DATABASES = {
    "default": dj_database_url.config(
        conn_max_age=600,
        ssl_require=ssl_require,  # <- ora controllato da ENV
    )
}

# Email backend (prod)
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"

# CORS (frontend separato)
CORS_ALLOW_ALL_ORIGINS = False
# Allow override via comma-separated env var (useful for local prod-like testing)
_cors_env = [h.strip() for h in os.getenv("CORS_ALLOWED_ORIGINS", "").split(",") if h.strip()]
if _cors_env:
    CORS_ALLOWED_ORIGINS = _cors_env
else:
    CORS_ALLOWED_ORIGINS = [
        "https://corsi.openpython.it",       # Frontend principale
        "https://lms-api-9tns.onrender.com", # Backend API
    ]

CORS_ALLOW_CREDENTIALS = True

# Cookie security
# Allow overriding secure flags in local prod-like runs via env vars (0/1)
SESSION_COOKIE_SECURE = os.getenv("SESSION_COOKIE_SECURE", "1") == "1"
CSRF_COOKIE_SECURE = os.getenv("CSRF_COOKIE_SECURE", "1") == "1"

# Debug logging per CSRF
print(f"DEBUG: CSRF_COOKIE_SECURE env var = {os.getenv('CSRF_COOKIE_SECURE', 'NOT_SET')}")
print(f"DEBUG: CSRF_COOKIE_SECURE setting = {CSRF_COOKIE_SECURE}")
print(f"DEBUG: CSRF_TRUSTED_ORIGINS = {CSRF_TRUSTED_ORIGINS}")
print(f"DEBUG: ALLOWED_HOSTS = {ALLOWED_HOSTS}")

# Cross-origin cookie settings for frontend on different domain
# When the frontend is hosted on a different origin (eg. corsi.openpython.it), 
# the browser will only send session/csrf cookies on cross-site requests if 
# SameSite=None and Secure is enabled.
# For admin panel on same domain, we need Lax
SESSION_COOKIE_SAMESITE = "Lax"  # Changed from None to Lax for admin
CSRF_COOKIE_SAMESITE = os.getenv("CSRF_COOKIE_SAMESITE", "Lax")  # Changed default

# CSRF Cookie domain and path settings for cross-origin
CSRF_COOKIE_HTTPONLY = False  # Must be False so frontend JS can read csrftoken
CSRF_COOKIE_NAME = 'csrftoken'
CSRF_HEADER_NAME = 'HTTP_X_CSRFTOKEN'
CSRF_COOKIE_AGE = 31449600  # 1 year

# Force CSRF cookie for admin panel (temporary debug)
CSRF_COOKIE_DOMAIN = None  # Let Django handle automatically
CSRF_USE_SESSIONS = False  # Ensure we use cookies, not sessions
CSRF_FAILURE_VIEW = 'django.views.csrf.csrf_failure'  # Default failure view

# Session cookie settings
SESSION_COOKIE_HTTPONLY = True  # Can stay True for security
SESSION_COOKIE_AGE = 1209600  # 2 weeks
SESSION_COOKIE_NAME = 'sessionid'

# Debug logging per Session
print(f"DEBUG: SESSION_COOKIE_SECURE env var = {os.getenv('SESSION_COOKIE_SECURE', 'NOT_SET')}")
print(f"DEBUG: SESSION_COOKIE_SECURE setting = {SESSION_COOKIE_SECURE}")
print(f"DEBUG: SESSION_COOKIE_SAMESITE = {SESSION_COOKIE_SAMESITE}")

# Force session settings for admin panel
SESSION_COOKIE_DOMAIN = None  # Let Django auto-detect
SESSION_SAVE_EVERY_REQUEST = True  # Save session on every request

# WhiteNoise: strict manifest can cause 500s if manifest is missing.
# Keep cache-busting benefits but avoid hard failures at runtime.
WHITENOISE_AUTOREFRESH = False
WHITENOISE_USE_FINDERS = False
WHITENOISE_MANIFEST_STRICT = False

# Stripe: enforcement in prod, ma consentiamo di bypassare durante il build
# impostando ENFORCE_STRIPE=0 (es. in build step su Render).
if os.getenv("ENFORCE_STRIPE", "1") == "1" and not STRIPE_SECRET_KEY:
    raise ImproperlyConfigured("STRIPE_SECRET_KEY environment variable is required for production")

# Forza DB system in prod
USE_DB_TEOCOIN_SYSTEM = True
TEOCOIN_SYSTEM = "database"

# Sentry
sentry_sdk.init(
    dsn=os.getenv("SENTRY_DSN"),
    integrations=[DjangoIntegration(), CeleryIntegration()],
    traces_sample_rate=0.1,
    send_default_pii=True,
    environment=ENVIRONMENT,
)

# Logging
# Crea la cartella logs se manca (evita crash all'avvio del FileHandler)
os.makedirs(BASE_DIR / "logs", exist_ok=True)

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {process:d} {thread:d} {message}",
            "style": "{",
        },
        "simple": {
            "format": "{levelname} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "file": {
            "level": "INFO",
            "class": "logging.FileHandler",
            "filename": BASE_DIR / "logs" / "api_performance.log",
            "formatter": "verbose",
        },
        "console": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            "formatter": "simple",
        },
    },
    "loggers": {
        "api_performance": {
            "handlers": ["file", "console"],
            "level": "INFO",
            "propagate": False,
        },
        # root logger should also print to console for container stdout parity
        "": {
            "handlers": ["console"],
            "level": "INFO",
        },
    },
}
