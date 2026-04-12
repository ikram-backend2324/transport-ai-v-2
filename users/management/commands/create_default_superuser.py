from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
import os

User = get_user_model()

class Command(BaseCommand):
    help = "Create default superuser if not exists"

    def handle(self, *args, **kwargs):
        username = os.environ.get("DJANGO_SUPERUSER_USERNAME")
        password = os.environ.get("DJANGO_SUPERUSER_PASSWORD")

        if not username or not password:
            self.stdout.write(self.style.WARNING("Superuser env variables not set"))
            return

        if User.objects.filter(username=username).exists():
            self.stdout.write(self.style.WARNING("Superuser already exists"))
            return

        User.objects.create_superuser(
            username=username,
            password=password
        )

        self.stdout.write(self.style.SUCCESS("Superuser created successfully"))