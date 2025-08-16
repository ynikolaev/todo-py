from __future__ import annotations

from aiogram_dialog import Dialog, StartMode, Window
from aiogram_dialog.widgets.kbd import Button, Row
from aiogram_dialog.widgets.text import Const

from app.dialogs.states import (
    CategoryCreateDlg,
    CategoryListDlg,
    CreateTaskDlg,
    MenuDlg,
)


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
menu_dialog = Dialog(menu_window)
