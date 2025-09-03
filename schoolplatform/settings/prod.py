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

_raw_csrf = [h.strip() for h in os.getenv("CSRF_TRUSTED_ORIGINS", "").split(",") if h.strip()]
CSRF_TRUSTED_ORIGINS = []
for origin in _raw_csrf:
    if not re.match(r"^https?://", origin):
        raise ImproperlyConfigured(
            f"CSRF_TRUSTED_ORIGINS must start with http:// or https:// (got: '{origin}')"
        )
    CSRF_TRUSTED_ORIGINS.append(origin)

# Allow disabling SSL requirement locally by setting DB_SSL_REQUIRE=0
_ssl_required = os.getenv("DB_SSL_REQUIRE", "1") == "1"
DATABASES = {
    "default": dj_database_url.config(conn_max_age=600, ssl_require=_ssl_required)
}

# Email backend (prod)
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"

# CORS (frontend separato)
CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOWED_ORIGINS = [
    "https://schoolplatform-frontend.onrender.com",  # FE
    "https://schoolplatform.onrender.com",           # BE (admin)
    # Nota: Render in genere non usa 'www.' per i subdomain; tienilo solo se realmente attivo.
    # "https://www.schoolplatform.onrender.com",
]

CORS_ALLOW_CREDENTIALS = True

# Cookie security
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

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
    },
}
