from __future__ import annotations

import logging
import math
from typing import TypedDict

from aiogram import Router, types
from aiogram.filters import Command
from aiogram.fsm.state import State, StatesGroup
from aiogram_dialog import Dialog, DialogManager, StartMode, Window
from aiogram_dialog.widgets.kbd import Button, Cancel, Row, Select
from aiogram_dialog.widgets.text import Const, Format

from app.infra.http import api_client
from app.widgets.vertical_select import VerticalSelect

logger = logging.getLogger(__name__)
router = Router(name=__name__)


PAGE_SIZE_DEFAULT = 10


# --- States ---
class CategoryListDlg(StatesGroup):
    list = State()


class CategoryTD(TypedDict):
    id: int
    name: str


async def fetch_page(manager: DialogManager, page: int, page_size: int):
    """Fetch a page from the backend. Returns (items, count, error_text)."""
    api_token = manager.middleware_data.get("api_token") or ""
    tg_user_id = manager.event.from_user.id if manager.event.from_user else None
    async with api_client(api_token) as client:
        r = await client.get(
            "api/categories/",
            params={"page": page, "page_size": page_size, "user_id": tg_user_id},
        )

    if r.status_code != 200:
        try:
            detail = r.json()
        except Exception:
            detail = r.text
        return [], 0, f"❌ Failed to load categories: {detail}"

    data = r.json()
    logger.info(data)
    items = data.get("results", []) or []
    count = int(data.get("count", len(items)))
    return items, count, None


# --- Getters & Handlers ---


async def list_getter(dialog_manager: DialogManager, **_):
    page = int(dialog_manager.dialog_data.get("page", 1))
    page_size = int(dialog_manager.dialog_data.get("page_size", PAGE_SIZE_DEFAULT))

    items, count, error = await fetch_page(dialog_manager, page, page_size)
    total_pages = max(1, math.ceil(count / page_size)) if page_size else 1
    page = max(1, min(page, total_pages))

    dialog_manager.dialog_data.update(
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        total_count=count,
    )

    normalized = [{"id": it.get("id"), "name": it.get("name", "—")} for it in items]

    return {
        "items": normalized,
        "page": page,
        "total_pages": total_pages,
        "total_count": count,
        "error_text": f"❌ {error}\n" if error else "",
    }


async def on_item_click(
    callback: types.CallbackQuery,
    widget: Select,
    manager: DialogManager,
    item_id: str,
):
    # Just a tiny toast for now; you can switch to a details state if needed
    await callback.answer(f"📂 Category ID: {item_id}", show_alert=False)


async def on_prev(_: types.CallbackQuery, __: Button, manager: DialogManager):
    page = int(manager.dialog_data.get("page", 1))
    if page > 1:
        manager.dialog_data["page"] = page - 1
    await manager.switch_to(CategoryListDlg.list)


async def on_next(_: types.CallbackQuery, __: Button, manager: DialogManager):
    page = int(manager.dialog_data.get("page", 1))
    total_pages = int(manager.dialog_data.get("total_pages", 1))
    if page < total_pages:
        manager.dialog_data["page"] = page + 1
    await manager.switch_to(CategoryListDlg.list)


async def on_refresh(_: types.CallbackQuery, __: Button, manager: DialogManager):
    # no changes, just re-render (will re-fetch in getter)
    await manager.switch_to(CategoryListDlg.list)


# --- Window ---

list_window = Window(
    Format(
        "🗂️ <b>Categories</b>\n"
        "Page {page}/{total_pages} • Total: {total_count}\n"
        "{error_text}"
        "\nSelect a category:"
    ),
    # Render current server page items as buttons
    VerticalSelect[CategoryTD](
        id="cat_select",
        items="items",
        item_id_getter=lambda x: str(x.get("id", "")),
        text=Format("📂 {item[name]}\n   <i>ID:</i> <code>{item[id]}</code>"),
        on_click=on_item_click,
    ),
    Row(
        Button(Const("◀ Prev"), id="prev", on_click=on_prev),
        Button(Const("🔄 Refresh"), id="refresh", on_click=on_refresh),
        Button(Const("Next ▶"), id="next", on_click=on_next),
    ),
    Row(
        Cancel(Const("❌ Close")),
    ),
    getter=list_getter,
    state=CategoryListDlg.list,
)

categories_list_dialog = Dialog(list_window)


# --- Command to start the dialog ---


@router.message(Command("list_categories"))
async def start_categories(message: types.Message, dialog_manager: DialogManager):
    # You can pass page_size via start_data if you want a different default
    await dialog_manager.start(
        CategoryListDlg.list,
        mode=StartMode.RESET_STACK,
        data={"page": 1, "page_size": PAGE_SIZE_DEFAULT},
    )
