import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

User = get_user_model()


class Command(BaseCommand):
    help = "Create/ensure bot service user."

    def handle(self, *args, **opts):
        username = os.getenv("TELEGRAM_BOT_SERVICE_USERNAME")
        password = os.getenv("TELEGRAM_BOT_SERVICE_PASSWORD")

        user, created = User.objects.get_or_create(
            username=username, defaults={"is_active": True, "is_staff": True}
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f"Created user {username}"))
        else:
            self.stdout.write(self.style.WARNING(f"User {username} already exists"))
        if password:
            user.set_password(password)
            user.save(update_fields=["password"])
