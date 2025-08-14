from django.contrib import admin

from .models import Category, Task, TelegramAccount, TelegramLinkCode


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
    list_display = ("user", "telegram_user_id", "chat_id", "linked_at")
    search_fields = ("user__username", "telegram_user_id")


@admin.register(TelegramLinkCode)
class TelegramLinkCodeAdmin(admin.ModelAdmin):
    list_display = ("code", "telegram_user_id", "expires_at", "used_at")
    search_fields = ("code", "telegram_user_id")
