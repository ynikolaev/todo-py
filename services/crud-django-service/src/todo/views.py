from django.db.models import QuerySet
from rest_framework import permissions, status, viewsets
from rest_framework.exceptions import ValidationError as DRFValidationError

from todo.api.pagination import DefaultPagination

from .models import Category, Task, TelegramAccount
from .serializers import CategorySerializer, TaskSerializer, TelegramAccountSerializer
from .tasks import schedule_due_notification


class IsOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        owner_id = getattr(obj, "user_id", None)
        return owner_id == request.user.id


class TelegramAccountViewSet(viewsets.ModelViewSet):
    queryset = TelegramAccount.objects.all().order_by("user_id")
    serializer_class = TelegramAccountSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = DefaultPagination


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all().select_related("tg")
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = DefaultPagination

    def get_queryset(self):
        qs = super().get_queryset()

        # Filter categories by the authenticated user's Telegram account (list - GET - /categories/)
        if self.action == "list":
            user_id = self.request.GET.get("tg_user_id")
            if not user_id:
                raise DRFValidationError(
                    {"tg_user_id": ["This field is required."]},
                    code=status.HTTP_400_BAD_REQUEST,
                )
            return qs.filter(tg__user_id=user_id).select_related("tg").order_by("name")
        return qs


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
        user_id = self.request.GET.get("tg_user_id")
        if not user_id:
            raise DRFValidationError(
                {"tg_user_id": ["This field is required."]},
                code=status.HTTP_400_BAD_REQUEST,
            )
        return (
            Task.objects.filter(
                tg__user_id=user_id
            )  # filter via related TelegramAccount field
            .select_related("tg")  # pre-fetch FK
            .prefetch_related("categories")  # prefetch M2M
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
