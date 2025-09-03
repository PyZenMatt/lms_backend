import pytest
from django.conf import settings

@pytest.fixture(autouse=True)
def use_sqlite_in_memory_db(settings):
    """Force tests to use in-memory sqlite DB to avoid Postgres dependency in CI/dev sandbox."""
    settings.DATABASES['default'] = {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
    return settings
