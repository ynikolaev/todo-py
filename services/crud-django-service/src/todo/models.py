from django.conf import settings
from django.db import models

from .id_gen import snowflake_id


class Category(models.Model):
    id = models.BigIntegerField(primary_key=True, default=snowflake_id, editable=False)
    name = models.CharField(max_length=120, unique=True)

    def __str__(self):
        return self.name


class TelegramAccount(models.Model):
    id = models.BigIntegerField(primary_key=True, default=snowflake_id, editable=False)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="tg"
    )
    chat_id = models.BigIntegerField(unique=True)


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
