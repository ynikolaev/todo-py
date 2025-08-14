# api/urls.py
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    BotLinkViewSet,
    CategoryViewSet,
    TaskViewSet,
    TelegramAccountViewSet,
)

router = DefaultRouter()
router.register(r"categories", CategoryViewSet, basename="category")
router.register(r"tasks", TaskViewSet, basename="task")
router.register(
    r"telegram-accounts", TelegramAccountViewSet, basename="telegram-account"
)
router.register(r"link", BotLinkViewSet, basename="link")

urlpatterns = [path("", include(router.urls))]
