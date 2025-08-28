from .base import *

# Test settings: use in-memory SQLite to avoid external DB dependencies
DEBUG = True

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
    'NAME': ':memory:',
    'ATOMIC_REQUESTS': False,
    }
}

# Use console email backend for tests
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Keep cache simple/local
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'test-cache',
    }
}
