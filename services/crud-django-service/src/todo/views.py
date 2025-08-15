from django.contrib.auth import get_user_model
from django.db.models import QuerySet
from rest_framework import permissions, status, viewsets
from rest_framework.exceptions import ValidationError as DRFValidationError

from todo.api.pagination import DefaultPagination

from .models import Category, Task
from .serializers import CategorySerializer, TaskSerializer
from .tasks import schedule_due_notification

User = get_user_model()


class IsOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        owner_id = getattr(obj, "user_id", None)
        return owner_id == request.user.id


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all().order_by("name")
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = DefaultPagination

    def get_queryset(self) -> QuerySet[Category]:  # type: ignore[override]
        user_id = self.request.GET.get("user_id")
        if not user_id:
            raise DRFValidationError(
                {"user_id": ["This field is required."]},
                code=status.HTTP_400_BAD_REQUEST,
            )
        return Category.objects.filter(user_id=user_id).order_by("name")


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
