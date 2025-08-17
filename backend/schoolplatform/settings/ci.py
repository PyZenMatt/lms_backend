# config/settings/ci.py
import os


# In CI vogliamo ambiente "prod-like"
DEBUG = False
ALLOWED_HOSTS = ["*"]

# --- Database: Postgres (variabili lette dall'ambiente del workflow) ---
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("POSTGRES_DB", "schoolplatform"),
        "USER": os.environ.get("POSTGRES_USER", "postgres"),
        "PASSWORD": os.environ.get("POSTGRES_PASSWORD", "postgres"),
        "HOST": os.environ.get("POSTGRES_HOST", "localhost"),
        "PORT": os.environ.get("POSTGRES_PORT", "5432"),
        "CONN_MAX_AGE": 0,  # connessioni brevi in CI
    }
}

# --- Cache: Redis (prod-like) ---
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": os.environ.get("REDIS_URL", "redis://localhost:6379/1"),
        "TIMEOUT": 300,
    }
}

# Email: niente invii reali in CI
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# Sicurezza minima per test CI
CSRF_TRUSTED_ORIGINS = []
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

# Logging essenziale (niente rumore)
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "root": {"handlers": ["console"], "level": "WARNING"},
}

# ⚠️ Blocca chiavi/valori dev: in dev.py c'erano default hardcoded per key/wallet.
# In CI NON mettiamo default: se servono, arrivano via env/Secrets.
PLATFORM_PRIVATE_KEY = os.environ.get("PLATFORM_PRIVATE_KEY")
ADMIN_PRIVATE_KEY = os.environ.get("ADMIN_PRIVATE_KEY")
PLATFORM_WALLET_ADDRESS = os.environ.get("PLATFORM_WALLET_ADDRESS")

# Usa TeoCoin su DB (come da dev), ma senza forzare valori sensibili
USE_DB_TEOCOIN_SYSTEM = os.environ.get(
    "USE_DB_TEOCOIN_SYSTEM", "True").lower() == "true"
