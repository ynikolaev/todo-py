from __future__ import annotations

import logging
import math
from typing import TypedDict, cast

from aiogram import Router, types
from aiogram.filters import Command
from aiogram_dialog import (
    Dialog,
    DialogManager,
    ShowMode,
    StartMode,
    SubManager,
    Window,
)
from aiogram_dialog.widgets.input import ManagedTextInput, TextInput
from aiogram_dialog.widgets.kbd import Button, ListGroup, Row, Start
from aiogram_dialog.widgets.text import Const, Format

from app.dialogs._states import CategoryCreateDlg, CategoryListDlg, CreateTaskDlg
from app.dialogs.menu import MenuDlg
from app.services.categories import CategoryDTO, CategoryService

logger = logging.getLogger(__name__)
router = Router(name=__name__)


PAGE_SIZE_DEFAULT = 3


# --- States ---
class CategoryTD(TypedDict):
    id: int
    name: str


# --- API client helper ---


async def api_fetch_page(manager: DialogManager, page: int, page_size: int):
    """Fetch a page from the backend. Returns (items, count, error_text)."""
    api_token = manager.middleware_data.get("api_token") or ""
    category_service = CategoryService(api_token=api_token)
    tg_user_id = manager.event.from_user.id if manager.event.from_user else None

    data = await category_service.get_categories(
        user_id=str(tg_user_id), page=page, page_size=page_size
    )

    items = data.get("results", []) or []
    count = int(data.get("count", len(items)))
    return items, count, None


async def api_delete_category(manager: DialogManager, category_id: str) -> None:
    api_token = manager.middleware_data.get("api_token") or ""
    category_service = CategoryService(api_token=api_token)
    await category_service.delete_category(category_id)


# --- Getters ---
async def edit_getter(dialog_manager: DialogManager, **_):
    category_id = dialog_manager.dialog_data.get("category_id")
    items = dialog_manager.dialog_data.get("items_cache", [])
    item = next((it for it in items if str(it["id"]) == category_id), {})
    return {
        "category_id": category_id,
        "category_name": item["name"] if item else "—",
    }


async def categories_getter(dialog_manager: DialogManager, **_):
    page = int(dialog_manager.dialog_data.get("page", 1))
    page_size = int(dialog_manager.dialog_data.get("page_size", PAGE_SIZE_DEFAULT))

    items, count, error = await api_fetch_page(dialog_manager, page, page_size)
    total_pages = max(1, math.ceil(count / page_size)) if page_size else 1
    page = max(1, min(page, total_pages))
    current_page_size = (page_size * page - page_size) + len(items)

    dialog_manager.dialog_data.update(
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        total_count=count,
    )

    normalized = [{"id": it.get("id"), "name": it.get("name", "—")} for it in items]
    dialog_manager.dialog_data["items_cache"] = normalized

    return {
        "items": normalized,
        "page_size": page_size,
        "current_page_size": current_page_size,
        "page": page,
        "total_pages": total_pages,
        "total_count": count,
        "error_text": f"❌ {error}\n" if error else "",
    }


# --- Handlers ---
async def on_name_entered(
    message: types.Message,
    widget: ManagedTextInput[str],
    manager: DialogManager,
    new_value: str,
):
    api_token = manager.middleware_data.get("api_token", "")
    category_id = manager.dialog_data["category_id"]
    category_service = CategoryService(api_token=api_token)
    category_dto = CategoryDTO(name=new_value)
    await category_service.update_category(category_id, category_dto)
    await message.answer(f"✅ Category renamed to: {new_value}")
    await manager.switch_to(CategoryListDlg.categories, show_mode=ShowMode.EDIT)


async def on_edit(
    callback: types.CallbackQuery,
    button: Button,
    manager: DialogManager,
):
    manager = cast(SubManager, manager)
    item_id = manager.item_id
    manager.dialog_data["category_id"] = item_id
    await callback.answer("Type new value below:")
    await manager.switch_to(CategoryListDlg.edit, show_mode=ShowMode.EDIT)


async def on_delete_request(
    callback: types.CallbackQuery,
    button: Button,
    manager: DialogManager,
):
    manager = cast(SubManager, manager)
    item_id = manager.item_id
    manager.dialog_data["category_id"] = item_id
    await manager.switch_to(CategoryListDlg.confirm_delete, show_mode=ShowMode.EDIT)


async def on_delete_confirm(
    callback: types.CallbackQuery,
    button: Button,
    manager: DialogManager,
):
    category_id = str(manager.dialog_data.get("category_id"))
    await api_delete_category(manager, category_id)
    await callback.answer("✅ Category deleted")
    await manager.switch_to(CategoryListDlg.categories, show_mode=ShowMode.EDIT)


async def on_prev(_: types.CallbackQuery, __: Button, manager: DialogManager):
    page = int(manager.dialog_data.get("page", 1))
    if page > 1:
        manager.dialog_data["page"] = page - 1
    await manager.switch_to(CategoryListDlg.categories, show_mode=ShowMode.EDIT)


async def on_next(_: types.CallbackQuery, __: Button, manager: DialogManager):
    page = int(manager.dialog_data.get("page", 1))
    total_pages = int(manager.dialog_data.get("total_pages", 1))
    if page < total_pages:
        manager.dialog_data["page"] = page + 1
    await manager.switch_to(CategoryListDlg.categories, show_mode=ShowMode.EDIT)


async def on_refresh(_: types.CallbackQuery, __: Button, manager: DialogManager):
    # no changes, just re-render (will re-fetch in getter)
    await manager.switch_to(CategoryListDlg.categories, show_mode=ShowMode.EDIT)


async def go_back_to_list(
    callback: types.CallbackQuery,
    button: Button,
    manager: DialogManager,
):
    await manager.switch_to(CategoryListDlg.categories, show_mode=ShowMode.EDIT)


async def on_new_task(c, b, m: DialogManager):
    manager = cast(SubManager, m)
    category_id = manager.item_id
    items = m.dialog_data.get("items_cache", [])
    item = next((it for it in items if str(it["id"]) == category_id), {})
    await m.start(
        CreateTaskDlg.title,
        data={"category_id": category_id, "category_name": item["name"]},
    )


async def go_back_to_menu(
    callback: types.CallbackQuery,
    button: Button,
    manager: DialogManager,
):
    await manager.start(MenuDlg.main, mode=StartMode.RESET_STACK)


# --- Widgets ---
categories_list = ListGroup(
    Row(
        Button(Format("{item[name]}"), id="view", on_click=on_new_task),
    ),
    Row(
        Button(Const("✏️"), id="edit", on_click=on_edit),
        Button(Const("🗑️"), id="del", on_click=on_delete_request),
    ),
    id="categories",
    items="items",
    item_id_getter=lambda x: str(x["id"]),
)

pagination_row = Row(
    Button(
        Const("⬅️ Prev"), id="prev", on_click=on_prev, when=lambda d, m, c: d["page"] > 1
    ),
    Button(Const("🔄 Refresh"), id="refresh", on_click=on_refresh),
    Button(
        Const("Next ➡️"),
        id="next",
        on_click=on_next,
        when=lambda d, m, c: d["page"] < d["total_pages"],
    ),
)


# --- Window ---
list_window = Window(
    Format("📂 Your Categories ({current_page_size}/{total_count})"),
    categories_list,
    pagination_row,
    Start(Const("❇️ New Category"), id="new_btn", state=CategoryCreateDlg.name),
    Button(Const("⬅️ Menu"), id="back", on_click=go_back_to_menu),
    state=CategoryListDlg.categories,
    getter=categories_getter,
)

edit_window = Window(
    Format("✏️ Editing category: {category_name}\nType new name below:"),
    TextInput[str](id="new_name", on_success=on_name_entered),
    Row(
        Button(Const("⬅️ Back"), id="back", on_click=go_back_to_list),
    ),
    state=CategoryListDlg.edit,
    getter=edit_getter,
)

confirm_delete_window = Window(
    Const("❗ Are you sure you want to delete this category?"),
    Row(
        Button(Const("✅ Yes"), id="confirm_del", on_click=on_delete_confirm),
        Button(Const("❌ No"), id="back", on_click=go_back_to_list),
    ),
    state=CategoryListDlg.confirm_delete,
)

dialog = Dialog(
    list_window,
    edit_window,
    confirm_delete_window,
)


# --- Command to start the dialog ---


@router.message(Command("list_categories"))
async def start_categories(message: types.Message, dialog_manager: DialogManager):
    await dialog_manager.start(
        CategoryListDlg.categories,
        mode=StartMode.RESET_STACK,
        data={"page": 1, "page_size": PAGE_SIZE_DEFAULT},
    )
