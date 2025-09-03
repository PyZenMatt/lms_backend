import re
from django.core.exceptions import ImproperlyConfigured

import dj_database_url
import sentry_sdk
from sentry_sdk.integrations.celery import CeleryIntegration
from sentry_sdk.integrations.django import DjangoIntegration

from .base import *

DEBUG = False

# Hosts / CSRF
ALLOWED_HOSTS = [h.strip() for h in os.getenv("ALLOWED_HOSTS", "").split(",") if h.strip()]
raw_csrf = [h.strip() for h in os.getenv("CSRF_TRUSTED_ORIGINS", "").split(",") if h.strip()]
CSRF_TRUSTED_ORIGINS = []
for origin in raw_csrf:
    if not re.match(r"^https?://", origin):
        raise ImproperlyConfigured(
            f"CSRF_TRUSTED_ORIGINS must start with http:// or https:// (got: '{origin}')"
        )
    CSRF_TRUSTED_ORIGINS.append(origin)

DATABASES = {
    "default": dj_database_url.config(conn_max_age=600, ssl_require=True)
}

# Email backend per prod
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"

# CORS in prod
CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOWED_ORIGINS = [
    "https://schoolplatform-frontend.onrender.com",
    "https://schoolplatform.onrender.com",
    "https://www.schoolplatform.onrender.com",
]
CORS_ALLOW_CREDENTIALS = True

# Cookie security
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# Stripe obbligatorio in prod
if not STRIPE_SECRET_KEY:
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

# Logging: console-only in Render (evita problemi di permessi/file)
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {"simple": {"format": "{levelname} {message}", "style": "{"}},
    "handlers": {"console": {"level": "INFO", "class": "logging.StreamHandler", "formatter": "simple"}},
    "root": {"handlers": ["console"], "level": "INFO"},
}
