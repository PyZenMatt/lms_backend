from django.core.management.base import BaseCommand
from django.conf import settings


class Command(BaseCommand):
    help = "Print BASE_DIR and static-related settings (for production diagnostics)"

    def handle(self, *args, **options):
        self.stdout.write(f"BASE_DIR={getattr(settings, 'BASE_DIR', None)}")
        self.stdout.write(f"STATIC_ROOT={getattr(settings, 'STATIC_ROOT', None)}")
        self.stdout.write(f"STATIC_URL={getattr(settings, 'STATIC_URL', None)}")
        self.stdout.write(f"STATICFILES_DIRS={getattr(settings, 'STATICFILES_DIRS', [])}")
        self.stdout.write(f"DEBUG={getattr(settings, 'DEBUG', None)}")
        self.stdout.write(f"STATICFILES_STORAGE={getattr(settings, 'STATICFILES_STORAGE', None)}")
