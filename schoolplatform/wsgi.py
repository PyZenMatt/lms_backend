"""
WSGI config for schoolplatform project.
https://docs.djangoproject.com/en/5.2/howto/deployment/wsgi/
"""

import os
from django.core.wsgi import get_wsgi_application
from whitenoise import WhiteNoise
from django.conf import settings

# Default ai settings di produzione
os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    os.getenv("DJANGO_SETTINGS_MODULE", "schoolplatform.settings.prod"),
)

application = get_wsgi_application()

# Cintura & bretelle: serviamo statici anche a livello WSGI
# (oltre al middleware) per evitare qualsiasi intercettazione anomala.
application = WhiteNoise(application, root=str(settings.STATIC_ROOT))
