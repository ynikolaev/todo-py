from datetime import UTC, datetime
from typing import cast

import requests
from celery import shared_task
from celery.app.task import Task as CeleryTask
from django.conf import settings
from django.utils import timezone

from .models import Task


@shared_task(
    bind=True,
    name="tasks.notify_task_due",
    autoretry_for=(requests.RequestException,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 5},
)
def notify_task_due(task_id: int) -> None:
    try:
        task = Task.objects.select_related("user").get(id=task_id)
        if task.is_done:
            return
        tg = getattr(task.user, "tg", None)
        if tg and tg.chat_id:
            text = f"⏰ Task due now:\n{task.title}\nCreated: {timezone.localtime(task.created_at)}"
            requests.post(
                f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage",
                json={"chat_id": tg.chat_id, "text": text},
                timeout=5,
            )
    except Task.DoesNotExist:
        pass


def schedule_due_notification(task_id: int, due_at: datetime) -> None:
    if due_at.tzinfo is None:
        # If due_at is naive, assume it's in the current timezone
        due_at = timezone.make_aware(due_at, timezone.get_current_timezone())
    eta_utc = due_at.astimezone(UTC)
    now_utc = timezone.now().astimezone(UTC)
    if eta_utc < now_utc:
        # If the due time is in the past, run immediately
        eta_utc = now_utc
    task_obj = cast(CeleryTask, notify_task_due)
    task_obj.apply_async(args=[task_id], eta=eta_utc)
