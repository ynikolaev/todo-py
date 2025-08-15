from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import QuerySet
from rest_framework import mixins, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet

from .models import Category, Task, TelegramAccount, TelegramLinkCode
from .serializers import CategorySerializer, TaskSerializer, TelegramAccountSerializer
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


class BotLinkViewSet(ViewSet):
    # permission_classes = [IsSignedBotCall, IsBotService]

    @action(detail=False, methods=["post"], url_path="start")
    def start(self, request):
        tg_id = int(request.data["telegram_user_id"])
        link = TelegramLinkCode.create_for(tg_id, ttl_minutes=10)
        return Response({"code": link.code, "expires_at": link.expires_at})

    @action(detail=False, methods=["post"], url_path="confirm")
    @transaction.atomic
    def confirm(self, request):
        tg_id = int(request.data["telegram_user_id"])
        code = str(request.data["code"])
        chat_id = request.data.get("chat_id")

        try:
            TelegramLinkCode.verify(code, tg_id)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        user, _ = User.objects.get_or_create(
            username=f"tg_{tg_id}", defaults={"is_active": True}
        )
        TelegramAccount.objects.update_or_create(
            telegram_user_id=tg_id, defaults={"user": user, "chat_id": chat_id}
        )
        return Response({"status": "linked", "user": user})
