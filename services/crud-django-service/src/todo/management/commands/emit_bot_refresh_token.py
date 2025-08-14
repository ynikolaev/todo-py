import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()


class Command(BaseCommand):
    help = "Create/ensure bot service user and write a refresh token to a file."

    def add_arguments(self, parser):
        parser.add_argument(
            "--out", required=True, help="Path to write the refresh token"
        )

    def handle(self, *args, **opts):
        username = os.getenv("TELEGRAM_BOT_SERVICE_USERNAME")
        password = os.getenv("TELEGRAM_BOT_SERVICE_PASSWORD")
        out = opts["out"]

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

        refresh = RefreshToken.for_user(user)
        print(f"Refresh token for {username}")
        os.makedirs(os.path.dirname(out), exist_ok=True)
        with open(out, "w") as f:
            f.write(str(refresh))
        self.stdout.write(self.style.SUCCESS(f"Wrote refresh token to {out}"))
