from __future__ import annotations

from typing import Any

from aiogram import Router, types
from aiogram.filters import Command
from aiogram_dialog import Dialog, DialogManager, StartMode

from app.dialogs._states import CreateTaskDlg
from app.dialogs.tasks.task_form import on_create_confirm, task_form_windows

router = Router(name=__name__)


async def on_start_create_task(start_data: Any, manager: DialogManager):
    default_id = start_data.get("category_id", None)
    if not default_id:
        print("No default category ID provided, skipping selection.", flush=True)
        return
    cat_select = manager.find("cat_select")
    if not cat_select:
        print("Category select widget not found, cannot set default ID.", flush=True)
        return
    print(f"Setting default category ID: {default_id}", flush=True)
    cat_select.set_checked([str(default_id)])


dialog = Dialog(*task_form_windows(on_create_confirm), on_start=on_start_create_task)


# --- Command to start the dialog ---
@router.message(Command("new_task"))
async def start_new_task(message: types.Message, dialog_manager: DialogManager):
    await dialog_manager.start(CreateTaskDlg.title, mode=StartMode.RESET_STACK)
