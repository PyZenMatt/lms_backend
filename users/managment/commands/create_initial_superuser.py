# your_app/management/commands/create_initial_superuser.py
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.conf import settings
import os

class Command(BaseCommand):
    help = "Create initial superuser from env vars if none exists (idempotent)."

    def handle(self, *args, **options):
        User = get_user_model()

        # Se c'è già almeno un superuser, non fare nulla
        if User.objects.filter(is_superuser=True).exists():
            self.stdout.write(self.style.WARNING("Superuser already exists. Skipping."))
            return

        username = os.environ.get("DJANGO_SUPERUSER_USERNAME")
        email = os.environ.get("DJANGO_SUPERUSER_EMAIL")
        password = os.environ.get("DJANGO_SUPERUSER_PASSWORD")

        missing = [k for k, v in {
            "DJANGO_SUPERUSER_USERNAME": username,
            "DJANGO_SUPERUSER_EMAIL": email,
            "DJANGO_SUPERUSER_PASSWORD": password,
        }.items() if not v]
        if missing:
            raise SystemExit(f"Missing env vars: {', '.join(missing)}")

        if User.objects.filter(username=username).exists():
            self.stdout.write(self.style.WARNING(f"User '{username}' exists but not superuser. Promoting."))
            u = User.objects.get(username=username)
            u.is_staff = True
            u.is_superuser = True
            if password:
                u.set_password(password)
            if email:
                u.email = email
            u.save()
            self.stdout.write(self.style.SUCCESS(f"User '{username}' promoted to superuser."))
            return

        # Crea il superuser
        u = User.objects.create_user(
            username=username,
            email=email or "",
            password=password
        )
        u.is_staff = True
        u.is_superuser = True
        u.save()
        self.stdout.write(self.style.SUCCESS(f"Superuser '{username}' created."))
