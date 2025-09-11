import os
from datetime import timedelta
from pathlib import Path

from dotenv import load_dotenv

# N.B. Mantengo la tua logica di BASE_DIR per non rompere riferimenti esistenti.
# Se la tua struttura è: project_root/schoolplatform/settings/base.py
# allora parent.parent.parent punta a project_root. Ok.
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Carica .env dal root se presente (non obbligatorio in prod)
load_dotenv(BASE_DIR / ".env")

SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret")
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

INSTALLED_APPS = [
    # Core Django
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Third parties
    "rest_framework",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",
    "django_filters",
    "corsheaders",
    "drf_spectacular",
    "modelcluster",
    "taggit",
    # Project apps
    "authentication",
    "core.apps.CoreConfig",
    "users",
    "courses",
    "rewards",
    "notifications",
    "blockchain",
    "payments",
    "services.apps.ServicesConfig",
]

# Ordine middleware consigliato:
# Security -> WhiteNoise -> CORS (il più in alto possibile, prima di CommonMiddleware) -> Session -> Common -> Csrf -> Auth -> Messages -> Clickjacking
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    # Middleware progetto (rimosso duplicato)
    "core.middleware.APITimingMiddleware",
    "core.middleware.GlobalErrorHandlingMiddleware",
]

SESSION_COOKIE_DOMAIN = None
CSRF_COOKIE_DOMAIN = None

ROOT_URLCONF = "schoolplatform.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [os.path.join(BASE_DIR, "templates")],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "schoolplatform.wsgi.application"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

SIMPLE_JWT = {
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "AUTH_HEADER_TYPES": ("Bearer",),
    "ACCESS_TOKEN_LIFETIME": timedelta(hours=1),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=1),
    "ALGORITHM": "HS256",
    "SIGNING_KEY": SECRET_KEY,
    "TOKEN_OBTAIN_SERIALIZER": "authentication.serializers.CustomTokenObtainPairSerializer",
}

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}

AUTH_USER_MODEL = "users.User"

# Static & Media
# Allow override via env to avoid conflicts with upstream routing
STATIC_URL = os.getenv("STATIC_URL", "/static/")
STATIC_ROOT = BASE_DIR / "staticfiles"

# Django 4.2+/5.x: preferisci STORAGES al vecchio STATICFILES_STORAGE
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

MEDIA_URL = "/media/"
MEDIA_ROOT = os.path.join(BASE_DIR, "media")

# WhiteNoise
# In dev si può voler aggiornare file statici a caldo; in prod resta False
WHITENOISE_AUTOREFRESH = ENVIRONMENT != "production"
# In dev, se serve, si può abilitare i finders (in prod Manifest resta la fonte)
WHITENOISE_USE_FINDERS = ENVIRONMENT != "production"

SESSION_ENGINE = "django.contrib.sessions.backends.cached_db"
SESSION_COOKIE_AGE = 3600
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"

LOGIN_REDIRECT_URL = "/app/dashboard/default"
LOGOUT_REDIRECT_URL = "/login/"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
TEST_RUNNER = "django.test.runner.DiscoverRunner"

# Blockchain config (comune)
POLYGON_AMOY_RPC_URL = os.getenv("POLYGON_AMOY_RPC_URL", "https://rpc-amoy.polygon.technology/")
TEOCOIN_CONTRACT_ADDRESS = os.getenv("TEOCOIN_CONTRACT_ADDRESS", "0x20D6656A31297ab3b8A87291Ed562D4228Be9ff8")
ADMIN_PRIVATE_KEY = os.getenv("ADMIN_PRIVATE_KEY")
ADMIN_WALLET_ADDRESS = os.getenv("ADMIN_WALLET_ADDRESS")

# Platform wallet address for TeoCoin payments (with minting permissions)
PLATFORM_WALLET_ADDRESS = os.getenv("PLATFORM_WALLET_ADDRESS", "0x3b72a4E942CF1467134510cA3952F01b63005044")
PLATFORM_PRIVATE_KEY = os.getenv("PLATFORM_PRIVATE_KEY")

# Reward Pool Configuration
REWARD_POOL_ADDRESS = os.getenv("REWARD_POOL_ADDRESS", "0x17051AB7603B0F7263BC86bF1b0ce137EFfdEcc1")
REWARD_POOL_PRIVATE_KEY = os.getenv("REWARD_POOL_PRIVATE_KEY", os.getenv("ADMIN_PRIVATE_KEY"))

# Payment configuration
TEOCOIN_EUR_RATE = 1  # 1 EUR = 1 TEO (1:1 rate for opportunities)
TEOCOIN_POOL_PERCENTAGE = 10  # 10% of fiat revenue goes to TeoCoin reward pool

# File upload
FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 250 * 1024 * 1024  # 250MB
FILE_UPLOAD_PERMISSIONS = 0o644
FILE_UPLOAD_DIRECTORY_PERMISSIONS = 0o755
FILE_UPLOAD_TEMP_DIR = None

# Default from email
DEFAULT_FROM_EMAIL = "no-reply@teocoin.io"

# Stripe config (comune, ma la segreta è obbligatoria solo in prod — vedi prod.py)
STRIPE_PUBLISHABLE_KEY = os.getenv("STRIPE_PUBLISHABLE_KEY")
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")

# Backend di autenticazione standard per admin Django
AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
]

# TeoCoin System Configuration
USE_DB_TEOCOIN_SYSTEM = os.getenv("USE_DB_TEOCOIN_SYSTEM", "True").lower() == "true"
# 'database' or 'blockchain'
TEOCOIN_SYSTEM = os.getenv("TEOCOIN_SYSTEM", "database")

# Reward System Configuration
REWARD_SYSTEM_BACKEND = "services.db_teocoin_service.DBTeoCoinService"
