from django.db.models import QuerySet
from rest_framework import mixins, permissions, viewsets
from rest_framework.response import Response

from .models import Category, Task, TelegramAccount
from .serializers import CategorySerializer, TaskSerializer, TelegramAccountSerializer
from .tasks import schedule_due_notification


class IsOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        owner_id = getattr(obj, "user_id", None)
        return owner_id == request.user.id


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all().order_by("name")
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticated]


class TaskViewSet(viewsets.ModelViewSet[Task, TaskSerializer]):
    """
    ViewSet for managing tasks.
    Allows listing, creating, updating, and deleting tasks.
    Tasks are filtered by the authenticated user.
    Due notifications are scheduled using Celery.
    """

    queryset: QuerySet[Task] = Task.objects.all()
    serializer_class: type[TaskSerializer] = TaskSerializer
    permission_classes: list[type[permissions.BasePermission]] = [
        permissions.IsAuthenticated,
        IsOwner,
    ]

    def get_queryset(self):  # type: ignore
        user = self.request.user
        return (
            Task.objects.filter(user=user)
            .select_related("user")
            .prefetch_related("categories")
            .order_by("-created_at")
        )

    def perform_create(self, serializer: TaskSerializer):
        task = serializer.save()
        if task.due_at:
            schedule_due_notification(task_id=task.id, due_at=task.due_at)

    def perform_update(self, serializer: TaskSerializer):
        task = serializer.save()
        if task.due_at:
            schedule_due_notification(task_id=task.id, due_at=task.due_at)


class TelegramAccountViewSet(
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet[TelegramAccount],
):
    """
    ViewSet for managing Telegram accounts linked to users.
    Allows creating, updating, and retrieving the Telegram account for the authenticated user.
    The `retrieve` method returns the Telegram account for the current user, creating it if it doesn't exist.
    The `create` and `update` methods allow setting or updating the Telegram chat ID.
    """

    serializer_class = TelegramAccountSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset: QuerySet[TelegramAccount] = TelegramAccount.objects.all()

    def retrieve(self, request, *args, **kwargs):
        obj, _ = TelegramAccount.objects.get_or_create(user=request.user)
        serializer = self.get_serializer(obj)
        return Response(serializer.data)
