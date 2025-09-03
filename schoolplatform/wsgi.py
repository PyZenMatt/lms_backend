"""
WSGI config for schoolplatform project.

It exposes the WSGI callable as a module-level variable named ``application``.
Docs: https://docs.djangoproject.com/en/5.2/howto/deployment/wsgi/
"""
import os
from django.core.wsgi import get_wsgi_application

# Usa prod come default, ma consenti override via env
os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    os.getenv("DJANGO_SETTINGS_MODULE", "schoolplatform.settings.prod"),
)

application = get_wsgi_application()
