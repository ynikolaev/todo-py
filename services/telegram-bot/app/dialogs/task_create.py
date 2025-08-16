from __future__ import annotations

import logging
from datetime import datetime

from aiogram import Router, types
from aiogram.filters import Command
from aiogram_dialog import Dialog, DialogManager, StartMode, Window
from aiogram_dialog.api.entities import ShowMode
from aiogram_dialog.widgets.input import ManagedTextInput, TextInput
from aiogram_dialog.widgets.kbd import Button, Cancel, Row, SwitchTo
from aiogram_dialog.widgets.text import Const, Format

from app.dialogs._states import CreateTaskDlg
from app.dialogs.menu import MenuDlg
from app.services.tasks import TaskDTO, TaskService
from app.services.telegram import TelegramAccountDTO

router = Router(name=__name__)


# --- Common cancel handler ---
async def on_cancel_to_menu(
    callback: types.CallbackQuery, button: Button, manager: DialogManager
):
    await callback.answer("❌ Cancelled")
    await manager.start(
        MenuDlg.main, mode=StartMode.RESET_STACK, show_mode=ShowMode.DELETE_AND_SEND
    )


# --- Step 1: Title input ---
async def on_title_input(
    message: types.Message,
    widget: ManagedTextInput,
    manager: DialogManager,
    text: str,
) -> None:
    title = (text or "").strip()

    if not title:
        await message.answer("⚠️ Title can’t be empty. Please send a title or /cancel.")
        return
    if len(title) > 255:
        await message.answer("⚠️ Title is too long (max 255 chars). Try a shorter one.")
        return

    manager.dialog_data["title"] = title
    await manager.next()


async def on_title_error(message: types.Message, *_):
    await message.answer("⚠️ Please send plain text for the title.")


# --- Step 2: Description input ---
async def on_description_input(
    message: types.Message,
    widget: ManagedTextInput,
    manager: DialogManager,
    text: str,
) -> None:
    manager.dialog_data["description"] = (text or "").strip()
    await manager.next()


async def on_description_error(message: types.Message, *_):
    await message.answer("⚠️ Please send plain text for the description.")


# --- Step 3: Due date input ---
async def on_due_date_input(
    message: types.Message,
    widget: ManagedTextInput,
    manager: DialogManager,
    text: str,
) -> None:
    if text.strip().lower() in ("", "none"):
        manager.dialog_data["due_at"] = None
        await manager.next()
        return

    try:
        due = datetime.strptime(text.strip(), "%Y-%m-%d %H:%M")
        manager.dialog_data["due_at"] = due.isoformat()
        await manager.next()
    except ValueError:
        await message.answer(
            "⚠️ Invalid format. Please send date & time in format: YYYY-MM-DD HH:MM"
        )


async def on_due_date_error(message: types.Message, *_):
    await message.answer("⚠️ Please send the due date in the correct format.")


# --- Step 4: Confirm ---
async def confirm_getter(dialog_manager: DialogManager, **_):
    return {
        "title": dialog_manager.dialog_data.get("title", "—"),
        "description": dialog_manager.dialog_data.get("description", "—"),
        "due_at": dialog_manager.dialog_data.get("due_at", "—"),
    }


async def on_confirm(
    callback: types.CallbackQuery,
    button: Button,
    manager: DialogManager,
) -> None:
    title: str = manager.dialog_data.get("title", "").strip()
    description: str = manager.dialog_data.get("description", "").strip()
    due_at = manager.dialog_data.get("due_at")

    if not callback.message or not title:
        await callback.answer("No task title provided.")
        return

    try:
        await callback.answer("⏳ Creating…", show_alert=False)
    except Exception as e:
        logging.warning("Failed to show toast notification", exc_info=e)

    api_token = manager.middleware_data.get("api_token") or ""
    task_service = TaskService(api_token=api_token)

    tg_dto = TelegramAccountDTO.from_callback(callback)
    task_dto = TaskDTO(title=title, description=description, due_at=due_at, tg=tg_dto)
    result = await task_service.create_task(task_dto)

    if "error" in result:
        await callback.message.answer(f"❌ Error creating task:\n{result['error']}")
        await manager.switch_to(state=CreateTaskDlg.title, show_mode=ShowMode.EDIT)
    else:
        await callback.message.answer(
            f"✅ Task '{result['title']}' created successfully!"
        )
        await manager.done()
        await manager.start(
            MenuDlg.main, mode=StartMode.RESET_STACK, show_mode=ShowMode.DELETE_AND_SEND
        )


# --- Windows ---
ask_title = Window(
    Const(
        "📝 <b>Create a new task</b>\n\n"
        "Send me the task title.\n"
        "• Tip: be specific\n"
        "• You can /cancel anytime"
    ),
    TextInput(id="title_input", on_success=on_title_input, on_error=on_title_error),
    Row(Button(Const("❌ Cancel"), id="cancel_btn", on_click=on_cancel_to_menu)),
    state=CreateTaskDlg.title,
)

ask_description = Window(
    Const("💬 Now send a description for the task (or just '-' to skip)."),
    TextInput(
        id="description_input",
        on_success=on_description_input,
        on_error=on_description_error,
    ),
    Row(Button(Const("❌ Cancel"), id="cancel_btn", on_click=on_cancel_to_menu)),
    state=CreateTaskDlg.description,
)

ask_due_date = Window(
    Const(
        "⏰ Send the due date & time in format: <b>YYYY-MM-DD HH:MM</b>\n"
        "Or send 'none' to skip."
    ),
    TextInput(
        id="due_at_input",
        on_success=on_due_date_input,
        on_error=on_due_date_error,
    ),
    Row(Button(Const("❌ Cancel"), id="cancel_btn", on_click=on_cancel_to_menu)),
    state=CreateTaskDlg.due_at,
)

confirm = Window(
    Format(
        "📋 <b>Review</b>\n"
        "Title: <b>{title}</b>\n"
        "Description: {description}\n"
        "Due at: {due_at}\n\n"
        "If everything looks good, press <b>Confirm</b>."
    ),
    Row(
        Button(Const("✅ Confirm"), id="confirm_btn", on_click=on_confirm),
        SwitchTo(Const("✏️ Edit"), id="edit_btn", state=CreateTaskDlg.title),
        Cancel(Const("❌ Cancel"), on_click=on_cancel_to_menu),
    ),
    getter=confirm_getter,
    state=CreateTaskDlg.confirm,
)

dialog = Dialog(ask_title, ask_description, ask_due_date, confirm)


# --- Command to start the dialog ---
@router.message(Command("new_task"))
async def start_new_task(message: types.Message, dialog_manager: DialogManager):
    await dialog_manager.start(CreateTaskDlg.title, mode=StartMode.RESET_STACK)
