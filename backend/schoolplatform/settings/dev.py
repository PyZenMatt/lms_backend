
from .base import *

DEBUG = True
ALLOWED_HOSTS = ['localhost', '127.0.0.1']
CSRF_TRUSTED_ORIGINS = ['http://localhost:3000', 'http://127.0.0.1:3000']

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': str(BASE_DIR / 'db.sqlite3'),
        'OPTIONS': {
            'timeout': 20,
            'check_same_thread': False,
        }
    }
}


# Email backend for dev
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
DEBUG_EMAIL_VERIFICATION = True

# CORS for dev
CORS_ALLOW_ALL_ORIGINS = True

# Cookie security for dev
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

# Debug toolbar
INTERNAL_IPS = ['127.0.0.1', 'localhost']
INSTALLED_APPS += ['debug_toolbar', 'django_extensions']
MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware']

# Logging (simple console for dev)
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'DEBUG',
    },
    'loggers': {
        'django.security': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'django.request': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'django.contrib.auth': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },

}

# Development blockchain configuration
# ⚠️ WARNING: These are test keys for development only, NEVER use in production
PLATFORM_PRIVATE_KEY = os.getenv(
    # Correct dev key
    'PLATFORM_PRIVATE_KEY', 'e1636922fa350bfe8ed929096d330eb70bbe3dc17dbb03dacdcf1dd668fc4255')
ADMIN_PRIVATE_KEY = os.getenv(
    'ADMIN_PRIVATE_KEY', 'e1636922fa350bfe8ed929096d330eb70bbe3dc17dbb03dacdcf1dd668fc4255')  # Same key

# Override platform wallet address to match our correct private key
PLATFORM_WALLET_ADDRESS = os.getenv(
    'PLATFORM_WALLET_ADDRESS', '0x3b72a4E942CF1467134510cA3952F01b63005044')

# Enable DB-based TeoCoin system for development
USE_DB_TEOCOIN_SYSTEM = os.getenv(
    'USE_DB_TEOCOIN_SYSTEM', 'True').lower() == 'true'
