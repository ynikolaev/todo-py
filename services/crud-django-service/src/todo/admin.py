from django.contrib import admin

from .models import Category, Task


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "user_id",
    )
    search_fields = (
        "name",
        "user_id",
    )


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "user_id", "is_done", "created_at", "due_at")
    list_filter = ("is_done", "categories", "user_id")
    search_fields = ("title", "description", "user_id")
