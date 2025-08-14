from rest_framework.routers import DefaultRouter

from .views import CategoryViewSet, TaskViewSet, TelegramAccountViewSet

router = DefaultRouter()
router.register(r"categories", CategoryViewSet, basename="category")
router.register(r"tasks", TaskViewSet, basename="task")
router.register(
    r"telegram-account", TelegramAccountViewSet, basename="telegram-account"
)

urlpatterns = router.urls
