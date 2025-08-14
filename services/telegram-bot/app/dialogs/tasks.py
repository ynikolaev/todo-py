from __future__ import annotations

from datetime import date

from aiogram import Router, types
from aiogram.filters import Command
from aiogram.fsm.state import State, StatesGroup
from aiogram_dialog import Dialog, DialogManager, StartMode, Window
from aiogram_dialog.api.entities import ChatEvent
from aiogram_dialog.widgets.input import ManagedTextInput, TextInput
from aiogram_dialog.widgets.kbd import Button, Calendar, Cancel, ManagedCalendar, Row
from aiogram_dialog.widgets.text import Const, Format

router = Router(name=__name__)


# --- Dialog states ---
class TaskDlg(StatesGroup):
    title = State()
    due = State()
    confirm = State()


# --- Widget callbacks & getters ---


async def on_title_input(
    message: types.Message,
    widget: ManagedTextInput,
    manager: DialogManager,
    title: str,
) -> None:
    title = title.strip()
    if not title:
        await message.answer("Title cannot be empty. Try again or /cancel.")
        return
    manager.dialog_data["title"] = title
    await manager.next()  # go to calendar


async def on_date_selected(
    event: ChatEvent,
    widget: ManagedCalendar,
    dialog_manager: DialogManager,
    date: date,
) -> None:
    dialog_manager.dialog_data["due"] = date
    await dialog_manager.next()


async def confirm_getter(dialog_manager: DialogManager, **_):
    title = dialog_manager.dialog_data.get("title", "—")
    due = dialog_manager.dialog_data.get("due")
    due_txt = due.isoformat() if due else "no date"

    return {
        "title": title,
        "due": due_txt,
    }


async def on_confirm(
    callback: types.CallbackQuery,
    button: Button,
    manager: DialogManager,
) -> None:
    # Step 5 will save to DB. For now, just show a final message.
    title: str = manager.dialog_data.get("title", "—")
    due: date | None = manager.dialog_data.get("due")
    due_txt = due.isoformat() if due else "no date"
    if not callback.message or not title:
        await callback.answer("No task title provided.")
        return
    await callback.message.answer(
        f"✅ Task created:\n<b>{title}</b>\nDue: <i>{due_txt}</i>"
    )
    await manager.done()


# --- Windows ---

ask_title = Window(
    Const("📝 <b>New Task</b>\nSend the task title:"),
    TextInput(id="title_input", on_success=on_title_input),
    Row(Cancel(Const("Cancel"))),
    state=TaskDlg.title,
)

pick_due = Window(
    Const("📅 Pick a due date (tap a day):"),
    Calendar(id="due_calendar", on_click=on_date_selected),
    Row(
        # If you want to allow skipping due date, add a button:
        Button(Const("Skip date"), id="skip_date", on_click=lambda c, b, m: m.next()),
        Cancel(Const("Cancel")),
    ),
    state=TaskDlg.due,
)

confirm = Window(
    Format("Confirm task:\n• <b>{title}</b>\n• Due: <i>{due}</i>"),
    Row(
        Button(Const("✅ Confirm"), id="confirm_btn", on_click=on_confirm),
        Cancel(Const("Cancel")),
    ),
    getter=confirm_getter,
    state=TaskDlg.confirm,
)

tasks_dialog_window = Dialog(ask_title, pick_due, confirm)


# --- Command to start the dialog ---
@router.message(Command("newtask"))
async def start_new_task(message: types.Message, dialog_manager: DialogManager):
    await dialog_manager.start(TaskDlg.title, mode=StartMode.RESET_STACK)
