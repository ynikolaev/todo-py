from __future__ import annotations

from aiogram import Router, types
from aiogram.filters import Command
from aiogram.fsm.state import State, StatesGroup
from aiogram_dialog import Dialog, DialogManager, StartMode, Window
from aiogram_dialog.widgets.input import ManagedTextInput, TextInput
from aiogram_dialog.widgets.kbd import Button, Cancel, Row
from aiogram_dialog.widgets.text import Const, Format

router = Router(name=__name__)  # will host the /profile_dialog command


# --- Dialog States ---
class ProfileDlg(StatesGroup):
    name = State()
    confirm = State()


# --- Handlers for the dialog ---
async def on_name_input(
    message: types.Message,
    widget: ManagedTextInput,
    manager: DialogManager,
    name: str,
) -> None:
    manager.dialog_data["name"] = name.strip()
    await manager.next()


async def on_confirm(
    callback: types.CallbackQuery,
    button: Button,
    manager: DialogManager,
) -> None:
    name = manager.dialog_data.get("name", "")
    cb_msg = callback.message
    if not cb_msg or not name:
        await callback.answer("No name provided.")
        return
    await cb_msg.answer(f"✅ Saved! Your display name is: <b>{name}</b>")
    await manager.done()


async def confirm_getter(dialog_manager: DialogManager, **_kwargs):
    return {"name": dialog_manager.dialog_data.get("name", "—")}


# --- Windows ---
ask_name = Window(
    Const("Let’s set your display name.\nPlease type your name:"),
    TextInput(id="name_input", on_success=on_name_input),
    Row(Cancel(Const("Cancel"))),
    state=ProfileDlg.name,
)

confirm_name = Window(
    Format("Confirm name: <b>{name}</b>"),
    Row(
        Button(Const("✅ Confirm"), id="confirm_btn", on_click=on_confirm),
        Cancel(Const("Cancel")),
    ),
    getter=confirm_getter,
    state=ProfileDlg.confirm,
)

# A Dialog is itself a Router in Aiogram-Dialog 2.x
profile_dialog_window = Dialog(ask_name, confirm_name)


# --- Command to start the dialog ---
@router.message(Command("profile_dialog"))
async def start_profile_dialog(message: types.Message, dialog_manager: DialogManager):
    await dialog_manager.start(ProfileDlg.name, mode=StartMode.RESET_STACK)
