from __future__ import annotations

import logging

from aiogram import Router, types
from aiogram.filters import Command
from aiogram.fsm.state import State, StatesGroup
from aiogram_dialog import Dialog, DialogManager, StartMode, Window
from aiogram_dialog.widgets.input import ManagedTextInput, TextInput
from aiogram_dialog.widgets.kbd import Button, Cancel, Row, SwitchTo
from aiogram_dialog.widgets.text import Const, Format

from app.infra.http import api_client

router = Router(name=__name__)


# --- Dialog states ---
class CreateDlg(StatesGroup):
    name = State()
    confirm = State()


# --- Widget callbacks & getters ---


async def on_name_input(
    message: types.Message,
    widget: ManagedTextInput,
    manager: DialogManager,
    name: str,
) -> None:
    title = (name or "").strip()

    # Soft validation
    if not title:
        await message.answer("⚠️ Name can’t be empty. Please send a name or /cancel.")
        return
    if len(title) > 120:
        await message.answer("⚠️ Name is too long (max 120 chars). Try a shorter one.")
        return

    manager.dialog_data["name"] = title
    await manager.next()


async def on_name_error(
    message: types.Message,
    widget: ManagedTextInput,
    manager: DialogManager,
    error: Exception,
) -> None:
    await message.answer("⚠️ I couldn’t read that. Please send plain text for the name.")


async def confirm_getter(dialog_manager: DialogManager, **_):
    return {
        "name": dialog_manager.dialog_data.get("name", "—"),
    }


async def on_confirm(
    callback: types.CallbackQuery,
    button: Button,
    manager: DialogManager,
) -> None:
    name: str = manager.dialog_data.get("name", "").strip()
    if not callback.message or not name:
        await callback.answer("No category name provided.")
        return
    # Non-blocking toast while we do the network call
    try:
        await callback.answer("⏳ Creating…", show_alert=False)
    except Exception as e:
        logging.warning("Failed to show toast notification", exc_info=e)
        pass

    api_token = manager.middleware_data.get("api_token") or ""
    user_id = callback.from_user.id
    async with api_client(api_token) as client:
        r = await client.post(
            "api/categories/", json={"name": name, "user_id": user_id}
        )

    if r.status_code != 201:
        try:
            detail = r.json()
        except Exception:
            detail = r.text
        if isinstance(detail, dict):
            detail = detail.get("non_field_errors", "Unknown error")
        await callback.message.answer(f"❌ Error creating category:\n{detail[0]}")
        return

    manager.dialog_data["id"] = r.json().get("id")
    await callback.answer("✅ Created!")
    await callback.message.answer(f"📂 Category “{name}” created successfully.")
    await manager.done()


# --- Windows ---

ask_name = Window(
    Const(
        "🗂️ <b>Create a new category</b>\n\n"
        "Send me the category name.\n"
        "• Tip: keep it short and clear\n"
        "• You can /cancel anytime"
    ),
    TextInput(
        id="title_input",
        on_success=on_name_input,
        on_error=on_name_error,
    ),
    Row(
        Cancel(Const("❌ Cancel")),
    ),
    state=CreateDlg.name,
)

confirm = Window(
    Format(
        "📋 <b>Review</b>\n"
        "Name: <b>{name}</b>\n"
        "If everything looks good, press <b>Confirm</b>."
    ),
    Row(
        Button(Const("✅ Confirm"), id="confirm_btn", on_click=on_confirm),
        SwitchTo(Const("✏️ Edit"), id="edit_btn", state=CreateDlg.name),
        Cancel(Const("❌ Cancel")),
    ),
    getter=confirm_getter,
    state=CreateDlg.confirm,
)

category_create_dialog_window = Dialog(ask_name, confirm)


# --- Command to start the dialog ---
@router.message(Command("new_category"))
async def start_new_category(message: types.Message, dialog_manager: DialogManager):
    await dialog_manager.start(CreateDlg.name, mode=StartMode.RESET_STACK)
