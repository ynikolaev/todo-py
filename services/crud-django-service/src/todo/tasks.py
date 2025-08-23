from datetime import datetime
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
def notify_task_due(_: CeleryTask, task_id: int) -> None:
    print(f"notify_task_due called for task_id={task_id}", flush=True)
    print(f"Current time: {timezone.localtime()}", flush=True)
    try:
        task = Task.objects.get(id=task_id)
        if task.is_done:
            return
        tg_account = task.tg
        if tg_account and tg_account.chat_id:
            text = (
                f"⏰ Task due now:\n"
                f"Title: {task.title}\n"
                f"Description: {task.description}\n"
                f"Created: {timezone.localtime(task.created_at).strftime('%Y-%m-%d %H:%M')}"
            )
            requests.post(
                f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage",
                json={"chat_id": tg_account.chat_id, "text": text},
                timeout=5,
            )
            Task.objects.filter(id=task_id, is_done=False).update(is_done=True)
    except Task.DoesNotExist:
        pass


def schedule_due_notification(task_id: int, due_at: datetime) -> None:
    if due_at.tzinfo is None:
        # If due_at is naive, assume it's in the current timezone
        due_at = timezone.make_aware(due_at, timezone.get_current_timezone())
    eta_utc = timezone.localtime(due_at)
    print(
        f"Scheduling notify_task_due for task_id={task_id} at {eta_utc} ({timezone.get_current_timezone_name()})",
        flush=True,
    )
    now_utc = timezone.localtime()
    print(
        f"Current time: {now_utc} ({timezone.get_current_timezone_name()})",
        flush=True,
    )
    if eta_utc < now_utc:
        # If the due time is in the past, run immediately
        eta_utc = now_utc
    task_obj = cast(CeleryTask, notify_task_due)
    task_obj.apply_async(args=[task_id], eta=eta_utc)
