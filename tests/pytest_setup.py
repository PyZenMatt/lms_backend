import os

# Ensure Django picks up the test settings module before pytest-django initializes
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schoolplatform.settings.test')
