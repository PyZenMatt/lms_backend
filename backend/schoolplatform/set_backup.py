from pathlib import Path
import os
from datetime import timedelta
from dotenv import load_dotenv
from django.core.exceptions import ImproperlyConfigured
import dj_database_url



# Carica il file .env che deve stare nella root del progetto (stesso livello di manage.py)
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / '.env')
ENVIRONMENT = os.getenv('ENVIRONMENT', 'development')
SECRET_KEY = os.getenv('SECRET_KEY')
DEBUG = os.getenv('DEBUG', 'False') == 'True'

# Allowed hosts (solo da variabile d'ambiente, nessun default su localhost)
ALLOWED_HOSTS = [h.strip() for h in os.getenv("ALLOWED_HOSTS", "").split(",") if h.strip()]

CSRF_TRUSTED_ORIGINS = [h.strip() for h in os.getenv("CSRF_TRUSTED_ORIGINS", "").split(",") if h.strip()]

# App
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # REST & JWT
    'rest_framework',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
    'django_filters',

    # Utility
    'corsheaders',
    'drf_spectacular',
    'modelcluster',
    'taggit',

    # App personalizzate
    'authentication',
    'core.apps.CoreConfig',
    'users',
    'courses',
    'rewards',
    'notifications',
    'blockchain.apps.BlockchainConfig',
    'services.apps.ServicesConfig',
]

# Debug toolbar (solo in development)
if DEBUG:
    INSTALLED_APPS += ['debug_toolbar',
                       'django_extensions']

# Middleware
MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    # WhiteNoise per servire statici in produzione
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'core.middleware.AutoJWTFromSessionMiddleware',
    'core.middleware.APITimingMiddleware',  # Performance monitoring
    'core.middleware.GlobalErrorHandlingMiddleware',  # Global error handling
]

# Debug toolbar middleware
if DEBUG:
    MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware']
    INTERNAL_IPS = ['127.0.0.1', 'localhost']

# URL
ROOT_URLCONF = 'schoolplatform.urls'

# Templates
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'schoolplatform.wsgi.application'

import dj_database_url

# Sviluppo: SQLite
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
        'OPTIONS': {
            'timeout': 20,
            'check_same_thread': False,
        }
    }
}

if DEBUG:
    # Ottimizzazioni per sviluppo
    DATABASES['default']['CONN_MAX_AGE'] = 60
    DATABASES['default']['CONN_HEALTH_CHECKS'] = True

else:
    # Produzione: PostgreSQL da DATABASE_URL
    DATABASES = {
        'default': dj_database_url.config(
            default=os.environ.get('DATABASE_URL'),
            conn_max_age=600,
            ssl_require=True
        )
    }

# Database connection pooling and optimization for development
if DEBUG:
    DATABASES['default']['CONN_MAX_AGE'] = 60  # Connection pooling for 60 seconds
    DATABASES['default']['CONN_HEALTH_CHECKS'] = True  # Health checks for connections

# Password
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# JWT Configuration
SIMPLE_JWT = {
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'AUTH_HEADER_TYPES': ('Bearer',),
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=1),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'TOKEN_OBTAIN_SERIALIZER': 'authentication.serializers.CustomTokenObtainPairSerializer',
}

# REST Framework
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}

# Auth user model
AUTH_USER_MODEL = 'users.User'

# Static & Media
# In produzione, WhiteNoise serve i file statici raccolti in STATIC_ROOT
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / "staticfiles"
# STATICFILES_DIRS serve solo se hai una cartella static custom fuori dalle app. Puoi riattivarla se serve:
# STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]

# Storage ottimizzato per WhiteNoise (compressione e cache busting)
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Sessioni
SESSION_ENGINE = 'django.contrib.sessions.backends.cached_db'
SESSION_COOKIE_AGE = 3600
SESSION_COOKIE_HTTPONLY = True

# CORS
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:3001", 
    "http://127.0.0.1:3001",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "http://localhost:8001",
    "http://127.0.0.1:8001",
    "https://schoolplatform-frontend.onrender.com",
    
]
SESSION_COOKIE_SAMESITE = "None"
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True

# Configurazioni CORS aggiuntive per il debug
CORS_ALLOW_ALL_ORIGINS = DEBUG  # Solo in sviluppo
CORS_ALLOWED_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
    'cache-control',
    'pragma',
]

CORS_ALLOW_METHODS = [
    'DELETE',
    'GET',
    'OPTIONS',
    'PATCH',
    'POST',
    'PUT',
]

# Preflight cache per migliorare le performance
CORS_PREFLIGHT_MAX_AGE = 86400

# Login/Logout redirect
LOGIN_REDIRECT_URL = '/app/dashboard/default'
LOGOUT_REDIRECT_URL = '/login/'

# Email (solo console in dev)
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
DEFAULT_FROM_EMAIL = 'no-reply@teocoin.io'
DEBUG_EMAIL_VERIFICATION = True

# Altri
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
TEST_RUNNER = 'django.test.runner.DiscoverRunner'



# Blockchain Configuration
POLYGON_AMOY_RPC_URL = os.getenv('POLYGON_AMOY_RPC_URL', 'https://rpc-amoy.polygon.technology/')
TEOCOIN_CONTRACT_ADDRESS = os.getenv('TEOCOIN_CONTRACT_ADDRESS', '0x20D6656A31297ab3b8A87291Ed562D4228Be9ff8')
ADMIN_PRIVATE_KEY = os.getenv('ADMIN_PRIVATE_KEY')
ADMIN_WALLET_ADDRESS = os.getenv('ADMIN_WALLET_ADDRESS')

# Reward Pool Configuration 
REWARD_POOL_ADDRESS = os.getenv('REWARD_POOL_ADDRESS', '0x17051AB7603B0F7263BC86bF1b0ce137EFfdEcc1')
REWARD_POOL_PRIVATE_KEY = os.getenv('REWARD_POOL_PRIVATE_KEY', os.getenv('ADMIN_PRIVATE_KEY'))

# =====================================
# 🚀 PERFORMANCE OPTIMIZATION CONFIG
# =====================================



# Celery Configuration
CELERY_BROKER_URL = 'redis://127.0.0.1:6379/0'
CELERY_RESULT_BACKEND = 'redis://127.0.0.1:6379/0'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'Europe/Rome'

# Sentry Configuration (only in production)
if not DEBUG:
    import sentry_sdk
    from sentry_sdk.integrations.django import DjangoIntegration
    from sentry_sdk.integrations.celery import CeleryIntegration
    
    sentry_sdk.init(
        dsn=os.getenv('SENTRY_DSN'),
        integrations=[
            DjangoIntegration(),
            CeleryIntegration()
        ],
        traces_sample_rate=0.1,
        send_default_pii=True,
        environment=ENVIRONMENT,
    )

# Database connection optimizations
if 'sqlite' not in DATABASES['default']['ENGINE']:
    DATABASES['default']['CONN_MAX_AGE'] = 600

# API Response Time Logging
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

# File Upload Settings - Support for larger video files
FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10MB - files larger than this will be saved to disk
DATA_UPLOAD_MAX_MEMORY_SIZE = 250 * 1024 * 1024  # 250MB - maximum total upload size
FILE_UPLOAD_PERMISSIONS = 0o644
FILE_UPLOAD_DIRECTORY_PERMISSIONS = 0o755

# Media file serving timeout for large files
FILE_UPLOAD_TEMP_DIR = None  # Use system default temp directory

# ========== STRIPE PAYMENT CONFIGURATION ==========
# Environment variables required - no defaults for security
STRIPE_PUBLISHABLE_KEY = os.getenv('STRIPE_PUBLISHABLE_KEY')
STRIPE_SECRET_KEY = os.getenv('STRIPE_SECRET_KEY')

# Validate that Stripe keys are configured
if not STRIPE_SECRET_KEY and not DEBUG:
    raise ImproperlyConfigured("STRIPE_SECRET_KEY environment variable is required for production")

# Platform wallet address for TeoCoin payments (with minting permissions)
PLATFORM_WALLET_ADDRESS = os.getenv('PLATFORM_WALLET_ADDRESS', '0x3b72a4E942CF1467134510cA3952F01b63005044')

# Payment configuration
TEOCOIN_EUR_RATE = 10  # 1 EUR = 10 TEO (base rate before discounts)
TEOCOIN_POOL_PERCENTAGE = 10  # 10% of fiat revenue goes to TeoCoin reward pool



# ⚡ Cache settings for optimal performance
CACHE_MIDDLEWARE_ALIAS = 'default'
CACHE_MIDDLEWARE_SECONDS = 300
CACHE_MIDDLEWARE_KEY_PREFIX = 'teoart'

# ========== TEOCOIN STAKING CONTRACT CONFIGURATION ==========

# TeoCoin Staking Contract Configuration  
TEOCOIN_STAKING_CONTRACT_ADDRESS = os.getenv('TEOCOIN_STAKING_CONTRACT', '0xd74fc566c0c5b83f95fd82e6866d8a7a6eaca7a9')

# Load staking contract ABI
def load_staking_abi():
    try:
        import json
        abi_path = os.path.join(BASE_DIR, 'blockchain', 'staking_abi.json')
        with open(abi_path, 'r') as f:
            return json.load(f)
    except:
        return []

TEOCOIN_STAKING_CONTRACT_ABI = load_staking_abi()

# ========== TEOCOIN DISCOUNT SYSTEM CONFIGURATION ==========

# TeoCoin Discount Contract Configuration
TEOCOIN_DISCOUNT_CONTRACT_ADDRESS = os.getenv('TEOCOIN_DISCOUNT_CONTRACT', '0xd30afec0bc6ac33e14a0114ec7403bbd746e88de')

# Load discount contract ABI
def load_discount_abi():
    try:
        import json
        abi_path = os.path.join(BASE_DIR, 'blockchain', 'discount_abi.json')
        with open(abi_path, 'r') as f:
            return json.load(f)
    except:
        return []

TEOCOIN_DISCOUNT_CONTRACT_ABI = load_discount_abi()

# Platform account private key for gas-free transactions
PLATFORM_PRIVATE_KEY = os.getenv('PLATFORM_PRIVATE_KEY')

# ========== GAS-FREE CONTRACTS CONFIGURATION ==========

# Gas-Free TeoCoin Contract Addresses (Phase 3)
TEOCOIN_DISCOUNT_GAS_FREE_CONTRACT_ADDRESS = os.getenv('TEOCOIN_DISCOUNT_GAS_FREE_CONTRACT', '0x998BbCAABe181843b440D6079596baee6367CAd9')
TEOCOIN_STAKING_GAS_FREE_CONTRACT_ADDRESS = os.getenv('TEOCOIN_STAKING_GAS_FREE_CONTRACT', '0xf76AcA8FCA2B9dE25D4c77C1343DED80280976D4')

# Platform Configuration for Gas-Free Operations
PLATFORM_ACCOUNT = os.getenv('PLATFORM_ACCOUNT')
POLYGON_RPC_URL = os.getenv('POLYGON_RPC_URL', 'https://rpc-amoy.polygon.technology/')

# ========== END GAS-FREE CONTRACTS CONFIGURATION ==========

# Discount system configuration
DISCOUNT_SYSTEM = {
    'REQUEST_TIMEOUT_HOURS': 2,
    'TEACHER_BONUS_PERCENT': 25,  # 25% bonus on top of student payment
    'MAX_DISCOUNT_PERCENT': 15,   # Maximum 15% discount
    'TEO_TO_EUR_RATE': 10,        # 1 TEO = 0.10 EUR discount value
    'MIN_DISCOUNT_PERCENT': 5,    # Minimum 5% discount
}

# Validate discount system configuration in production
if not DEBUG and TEOCOIN_DISCOUNT_CONTRACT_ADDRESS and not PLATFORM_PRIVATE_KEY:
    raise ImproperlyConfigured("PLATFORM_PRIVATE_KEY is required when discount system is enabled")

# ========== END TEOCOIN DISCOUNT CONFIGURATION ==========

# Gas-Free V2 Contract Addresses (DEPLOYED)
DISCOUNT_CONTRACT_V2_ADDRESS = os.getenv('DISCOUNT_CONTRACT_V2_ADDRESS', '')
STAKING_CONTRACT_V2_ADDRESS = os.getenv('STAKING_CONTRACT_V2_ADDRESS', '')
TEO_TOKEN_ADDRESS = os.getenv('TEO_TOKEN_ADDRESS', '')
REWARD_POOL_ADDRESS = os.getenv('REWARD_POOL_ADDRESS', '')

# Enable gas-free mode
GAS_FREE_MODE_ENABLED = os.getenv('GAS_FREE_MODE_ENABLED', 'True').lower() == 'true'

# Platform gas monitoring
PLATFORM_MATIC_THRESHOLD = float(os.getenv('PLATFORM_MATIC_THRESHOLD', '1.0'))

# Test mode indicator
GAS_FREE_TEST_MODE = os.getenv('GAS_FREE_TEST_MODE', 'True').lower() == 'true'

# ===== DB-BASED TEOCOIN SYSTEM =====
# Enable DB-based TeoCoin system instead of blockchain operations
USE_DB_TEOCOIN_SYSTEM = os.getenv('USE_DB_TEOCOIN_SYSTEM', 'True').lower() == 'true'
