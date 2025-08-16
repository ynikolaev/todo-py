from __future__ import annotations

from aiogram import Router, types
from aiogram.filters import Command
from aiogram_dialog import Dialog, DialogManager, StartMode, Window
from aiogram_dialog.widgets.kbd import Button, Row
from aiogram_dialog.widgets.text import Const

from app.dialogs._states import (
    CategoryCreateDlg,
    CategoryListDlg,
    CreateTaskDlg,
    MenuDlg,
)

router = Router(name=__name__)


async def to_categories(_, __, c):
    await c.start(CategoryListDlg.categories, mode=StartMode.RESET_STACK)


async def to_create_new_task(_, __, c):
    await c.start(CreateTaskDlg.title, mode=StartMode.RESET_STACK)


async def to_create_new_category(_, __, c):
    await c.start(CategoryCreateDlg.name, mode=StartMode.RESET_STACK)


menu_window = Window(
    Const("📋 <b>Main Menu</b>\nChoose an option:"),
    Row(
        Button(
            Const("👀 Show categories"),
            id="list_categories",
            on_click=to_categories,
        ),
    ),
    Row(
        Button(
            Const("🔔 Create a new task"), id="new_task", on_click=to_create_new_task
        ),
    ),
    Row(
        Button(
            Const("📂 Create a new category"),
            id="new_category",
            on_click=to_create_new_category,
        ),
    ),
    state=MenuDlg.main,
)
dialog = Dialog(menu_window)


@router.message(Command("main"))
async def start_categories(message: types.Message, dialog_manager: DialogManager):
    await dialog_manager.start(
        MenuDlg.main,
        mode=StartMode.RESET_STACK,
    )
