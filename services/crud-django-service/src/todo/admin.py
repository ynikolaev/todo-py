from django.contrib import admin

from .models import Category, Task


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "tg",
    )
    search_fields = ("name",)


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "is_done", "created_at", "due_at", "tg")
    list_filter = ("is_done", "categories", "tg")
    search_fields = ("title", "description")
