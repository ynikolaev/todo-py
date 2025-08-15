from django.db import models

from .id_gen import snowflake_id


class Category(models.Model):
    id = models.BigIntegerField(primary_key=True, default=snowflake_id, editable=False)
    name = models.CharField(max_length=120, null=False, blank=False)
    user_id = models.BigIntegerField(null=False, blank=False, default=0)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user_id", "name"], name="unique_user_category_name"
            )
        ]

    def __str__(self):
        return self.name


class Task(models.Model):
    id = models.BigIntegerField(primary_key=True, default=snowflake_id, editable=False)
    user_id = models.BigIntegerField(null=False, blank=False, default=0)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    categories = models.ManyToManyField(Category, related_name="tasks", blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    due_at = models.DateTimeField(null=True, blank=True)
    is_done = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.title} (#{self.id})"
