import re

import dj_database_url
import sentry_sdk
from sentry_sdk.integrations.celery import CeleryIntegration
from sentry_sdk.integrations.django import DjangoIntegration

from .base import *

DEBUG = False

# Parse ALLOWED_HOSTS and CSRF_TRUSTED_ORIGINS, ignore empty, strip, and validate scheme for CSRF
ALLOWED_HOSTS = [h.strip() for h in os.getenv(
    'ALLOWED_HOSTS', '').split(',') if h.strip()]
raw_csrf = [h.strip() for h in os.getenv(
    'CSRF_TRUSTED_ORIGINS', '').split(',') if h.strip()]
CSRF_TRUSTED_ORIGINS = []
for origin in raw_csrf:
    if not re.match(r'^https?://', origin):
        raise ImproperlyConfigured(
            f"CSRF_TRUSTED_ORIGINS must start with http:// or https:// (got: '{origin}')")
    CSRF_TRUSTED_ORIGINS.append(origin)

DATABASES = {
    'default': dj_database_url.config(conn_max_age=600, ssl_require=True)
}


# Email backend for prod
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

# CORS for prod - frontend is served from different origin
CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOWED_ORIGINS = [
    "https://schoolplatform-frontend.onrender.com",  # Frontend origin
    # Backend origin (for admin)
    "https://schoolplatform.onrender.com",
    "https://www.schoolplatform.onrender.com",       # www variant
]

# Allow credentials for cross-origin requests
CORS_ALLOW_CREDENTIALS = True

# Cookie security for prod
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# Stripe: enforce secret key in prod
if not STRIPE_SECRET_KEY:
    raise ImproperlyConfigured(
        "STRIPE_SECRET_KEY environment variable is required for production")

# TeoCoin System Configuration for Production
USE_DB_TEOCOIN_SYSTEM = True  # Force DB system in production
TEOCOIN_SYSTEM = 'database'   # Use database, not blockchain for internal operations

# Sentry (only prod)
sentry_sdk.init(
    dsn=os.getenv('SENTRY_DSN'),
    integrations=[DjangoIntegration(), CeleryIntegration()],
    traces_sample_rate=0.1,
    send_default_pii=True,
    environment=ENVIRONMENT,
)

# Logging (file + console for prod)
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'api_performance.log',
            'formatter': 'verbose',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    'loggers': {
        'api_performance': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}
