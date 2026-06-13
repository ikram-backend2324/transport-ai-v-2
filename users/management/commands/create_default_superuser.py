from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
import os

User = get_user_model()


class Command(BaseCommand):
    help = "Create or promote a default superuser using env variables."

    def handle(self, *args, **kwargs):
        username = os.environ.get("DJANGO_SUPERUSER_USERNAME")
        password = os.environ.get("DJANGO_SUPERUSER_PASSWORD")
        email = os.environ.get("DJANGO_SUPERUSER_EMAIL", "")

        if not username or not password:
            self.stdout.write(self.style.WARNING(
                "DJANGO_SUPERUSER_USERNAME / DJANGO_SUPERUSER_PASSWORD not set — skipping."
            ))
            return

        existing = User.objects.filter(username=username).first()
        if existing:
            changed = False
            if not existing.is_superuser:
                existing.is_superuser = True
                changed = True
            if not existing.is_staff:
                existing.is_staff = True
                changed = True
            if getattr(existing, "role", None) != "admin":
                existing.role = "admin"
                changed = True
            if email and not existing.email:
                existing.email = email
                changed = True
            if changed:
                existing.save()
                self.stdout.write(self.style.SUCCESS(
                    f"Existing user '{username}' promoted to admin."
                ))
            else:
                self.stdout.write(self.style.WARNING(
                    f"Superuser '{username}' already exists — nothing to do."
                ))
            return

        User.objects.create_superuser(
            username=username,
            email=email,
            password=password,
            role="admin",
        )
        self.stdout.write(self.style.SUCCESS(
            f"Superuser '{username}' created successfully."
        ))
