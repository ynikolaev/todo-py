from django.contrib import admin

from .models import Category, Task, TelegramAccount


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("id", "name")
    search_fields = ("name",)


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "user", "is_done", "created_at", "due_at")
    list_filter = ("is_done", "categories")
    search_fields = ("title", "description")


@admin.register(TelegramAccount)
class TelegramAccountAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "chat_id")
