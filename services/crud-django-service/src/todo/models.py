import secrets
from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone

from .id_gen import snowflake_id


class Category(models.Model):
    id = models.BigIntegerField(primary_key=True, default=snowflake_id, editable=False)
    name = models.CharField(max_length=120, unique=True)

    def __str__(self):
        return self.name


class Task(models.Model):
    id = models.BigIntegerField(primary_key=True, default=snowflake_id, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="tasks"
    )
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    categories = models.ManyToManyField(Category, related_name="tasks", blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    due_at = models.DateTimeField(null=True, blank=True)
    is_done = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.title} (#{self.id})"


class TelegramAccount(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    telegram_user_id = models.BigIntegerField(unique=True, default=0)
    chat_id = models.BigIntegerField(null=True, blank=True)
    linked_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.user.id} ↔ {self.telegram_user_id}"


class TelegramLinkCode(models.Model):
    code = models.CharField(max_length=12, unique=True)
    telegram_user_id = models.BigIntegerField()
    expires_at = models.DateTimeField()
    used_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["telegram_user_id"]),
            models.Index(fields=["expires_at"]),
        ]

    @classmethod
    def create_for(
        cls, telegram_user_id: int, ttl_minutes: int = 10
    ) -> "TelegramLinkCode":
        code = secrets.token_hex(4)  # 8 hex chars
        expires_at = timezone.now() + timedelta(minutes=ttl_minutes)
        return cls.objects.create(
            code=code, telegram_user_id=telegram_user_id, expires_at=expires_at
        )

    @classmethod
    def verify(cls, code: str, telegram_user_id: int) -> "TelegramLinkCode":
        obj = cls.objects.select_for_update().get(code=code)
        if obj.telegram_user_id != telegram_user_id:
            raise ValueError("Code / telegram_user_id mismatch")
        if obj.used_at is not None:
            raise ValueError("Code already used")
        if obj.expires_at <= timezone.now():
            raise ValueError("Code expired")
        obj.used_at = timezone.now()
        obj.save(update_fields=["used_at"])
        return obj
