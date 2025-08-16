from django.db import models

from .id_gen import snowflake_id


class Category(models.Model):
    id = models.BigIntegerField(primary_key=True, default=snowflake_id, editable=False)
    name = models.CharField(max_length=120, null=False, blank=False)
    tg = models.ForeignKey(
        "TelegramAccount",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="categories",
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["name", "tg"], name="unique_category_per_tg"
            )
        ]

    def __str__(self):
        return self.name


class Task(models.Model):
    id = models.BigIntegerField(primary_key=True, default=snowflake_id, editable=False)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    categories = models.ManyToManyField(Category, related_name="tasks", blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    due_at = models.DateTimeField(null=True, blank=True)
    is_done = models.BooleanField(default=False)
    tg = models.ForeignKey(
        "TelegramAccount",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="tasks",
    )

    def __str__(self):
        return f"{self.title} (#{self.id})"


class TelegramAccount(models.Model):
    @staticmethod
    def update_if_different(tg_account: "TelegramAccount", tg_data: dict) -> None:
        # If account exists but fields differ, update them
        fields_to_update = {}
        if tg_account.chat_id != tg_data["chat_id"]:
            fields_to_update["chat_id"] = tg_data["chat_id"]

        new_username = tg_data.get("tg_username")
        if new_username and tg_account.tg_username != new_username:
            fields_to_update["tg_username"] = new_username

        if fields_to_update:
            for field, value in fields_to_update.items():
                setattr(tg_account, field, value)
            tg_account.save(update_fields=list(fields_to_update.keys()))

    # Unique identifier for the user in Telegram (editable=True for API compatibility)
    user_id = models.BigIntegerField(primary_key=True, default=0, editable=True)
    chat_id = models.BigIntegerField(null=False, blank=False, unique=True)
    tg_username = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return f"Telegram Account {self.user_id} - {self.tg_username or self.chat_id}"

    class Meta:
        verbose_name = "Telegram Account"
        verbose_name_plural = "Telegram Accounts"
