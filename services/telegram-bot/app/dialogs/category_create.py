from __future__ import annotations

import logging

from aiogram import Router, types
from aiogram.filters import Command
from aiogram_dialog import Dialog, DialogManager, StartMode, Window
from aiogram_dialog.api.entities import ShowMode
from aiogram_dialog.widgets.input import ManagedTextInput, TextInput
from aiogram_dialog.widgets.kbd import Button, Cancel, Row, SwitchTo
from aiogram_dialog.widgets.text import Const, Format

from app.dialogs._states import CategoryCreateDlg
from app.dialogs.menu import MenuDlg
from app.services.categories import CategoryDTO, CategoryService
from app.services.telegram import TelegramAccountDTO

router = Router(name=__name__)


# --- Widget callbacks & getters ---


async def on_cancel_to_menu(
    callback: types.CallbackQuery, button: Button, manager: DialogManager
):
    await callback.answer("❌ Cancelled")
    await manager.start(
        MenuDlg.main, mode=StartMode.RESET_STACK, show_mode=ShowMode.DELETE_AND_SEND
    )


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

    try:
        await callback.answer("⏳ Creating…", show_alert=False)
    except Exception as e:
        logging.warning("Failed to show toast notification", exc_info=e)
        pass

    api_token = manager.middleware_data.get("api_token") or ""
    category_service = CategoryService(api_token=api_token)

    tg_dto = TelegramAccountDTO.from_callback(callback)
    category_dto = CategoryDTO(name=name, tg=tg_dto)
    result = await category_service.create_category(category_dto)
    if "error" in result:
        await callback.message.answer(f"❌ Error creating category:\n{result['error']}")
        await manager.switch_to(state=CategoryCreateDlg.name, show_mode=ShowMode.EDIT)
    else:
        await callback.message.answer(
            f"📂 Category '{result['name']}' created successfully!"
        )
        await manager.done()
        await manager.start(
            MenuDlg.main, mode=StartMode.RESET_STACK, show_mode=ShowMode.DELETE_AND_SEND
        )


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
    Row(Button(Const("❌ Cancel"), id="cancel_btn", on_click=on_cancel_to_menu)),
    state=CategoryCreateDlg.name,
)

confirm = Window(
    Format(
        "📋 <b>Review</b>\n"
        "Name: <b>{name}</b>\n"
        "If everything looks good, press <b>Confirm</b>."
    ),
    Row(
        Button(Const("✅ Confirm"), id="confirm_btn", on_click=on_confirm),
        SwitchTo(Const("✏️ Edit"), id="edit_btn", state=CategoryCreateDlg.name),
        Cancel(Const("❌ Cancel"), on_click=on_cancel_to_menu),
    ),
    getter=confirm_getter,
    state=CategoryCreateDlg.confirm,
)

dialog = Dialog(ask_name, confirm)


# --- Command to start the dialog ---
@router.message(Command("new_category"))
async def start_new_category(message: types.Message, dialog_manager: DialogManager):
    await dialog_manager.start(CategoryCreateDlg.name, mode=StartMode.RESET_STACK)
