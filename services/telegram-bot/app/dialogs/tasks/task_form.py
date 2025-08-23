import logging
from datetime import datetime
from operator import itemgetter

from aiogram import types
from aiogram_dialog import DialogManager, ShowMode, StartMode, Window
from aiogram_dialog.widgets.input import ManagedTextInput, TextInput
from aiogram_dialog.widgets.kbd import (
    Button,
    Cancel,
    Multiselect,
    Row,
    ScrollingGroup,
    Start,
    SwitchTo,
)
from aiogram_dialog.widgets.text import Const, Format

from app.dialogs._states import CategoryCreateDlg, CreateTaskDlg, MenuDlg
from app.services.categories import CategoryService
from app.services.tasks import TaskDTO, TaskService
from app.services.telegram import TelegramAccountDTO


# --- Windows ---
def ask_title():
    return Window(
        Const("📝 <b>Create a new task</b>"),
        Format("Category: <b>{category_name}</b>\n\n", when="category_name"),
        Const("Send me the task title.\n• Tip: be specific\n• You can /cancel anytime"),
        TextInput(id="title_input", on_success=on_title_input, on_error=on_title_error),
        Row(
            Button(
                Const("❌ Cancel"),
                id="cancel_btn",
                on_click=on_cancel_to_menu,
                when="no_category",
            )
        ),
        Cancel(Const("❌ Cancel"), show_mode=ShowMode.EDIT, when="has_category"),
        state=CreateTaskDlg.title,
        getter=default_category_getter,
    )


def categories_multiselect():
    return Multiselect(
        checked_text=Format("✅ {item[name]}"),
        unchecked_text=Format("⬜ {item[name]}"),
        id="cat_select",
        item_id_getter=lambda x: str(x["id"]),
        items="categories",
        min_selected=1,
    )


def scrolling_categories():
    return ScrollingGroup(
        categories_multiselect(),
        id="cats_scroll",
        width=1,
        height=6,  # show up to 6 items at once
        when=lambda data, _, __: bool(data["categories"]),
    )


def select_categories_window():
    return Window(
        Const(
            "Choose categories for your task (you can select multiple):",
            when=lambda data, _, __: bool(data["categories"]),
        ),
        Const(
            "📝 <b>There are no available categories</b>",
            when=lambda data, _, __: not bool(data["categories"]),
        ),
        scrolling_categories(),
        Row(
            Button(
                Const("✅ Confirm"), id="confirm_btn", on_click=on_categories_chosen
            ),
            Button(
                Const("❌ Cancel"),
                id="cancel_btn",
                on_click=on_cancel_to_menu,
                when="no_category",
            ),
            Cancel(Const("❌ Cancel"), show_mode=ShowMode.EDIT, when="has_category"),
            when=lambda data, _, __: bool(data["categories"]),
        ),
        Row(
            Start(Const("❇️ New Category"), id="new_btn", state=CategoryCreateDlg.name),
            Button(
                Const("❌ Cancel"),
                id="cancel_btn",
                on_click=on_cancel_to_menu,
                when="no_category",
            ),
            when=lambda data, _, __: not bool(data["categories"]),
        ),
        state=CreateTaskDlg.categories,
        getter=[get_categories_from_api, default_category_getter],
    )


def ask_description():
    return Window(
        Const("💬 Now send a description for the task (or just '-' to skip)."),
        TextInput(
            id="description_input",
            on_success=on_description_input,
            on_error=on_description_error,
        ),
        Button(
            Const("❌ Cancel"),
            id="cancel_btn",
            on_click=on_cancel_to_menu,
            when="no_category",
        ),
        Cancel(Const("❌ Cancel"), show_mode=ShowMode.EDIT, when="has_category"),
        state=CreateTaskDlg.description,
        getter=default_category_getter,
    )


def ask_due_date():
    return Window(
        Const(
            "⏰ Send the due date & time in format: <b>YYYY-MM-DD HH:MM</b>\n"
            "Or send 'none' to skip."
        ),
        TextInput(
            id="due_at_input",
            on_success=on_due_date_input,
            on_error=on_due_date_error,
        ),
        Button(
            Const("❌ Cancel"),
            id="cancel_btn",
            on_click=on_cancel_to_menu,
            when="no_category",
        ),
        Cancel(Const("❌ Cancel"), show_mode=ShowMode.EDIT, when="has_category"),
        state=CreateTaskDlg.due_at,
        getter=default_category_getter,
    )


def confirm(confirm_handler):
    return Window(
        Format(
            "📋 <b>Review</b>\n"
            "Title: <b>{title}</b>\n"
            "Description: {description}\n"
            "Categories: {categories}\n"
            "Due at: {due_at}\n\n"
            "If everything looks good, press <b>Confirm</b>."
        ),
        Row(
            Button(Const("✅ Confirm"), id="confirm_btn", on_click=confirm_handler),
            SwitchTo(Const("✏️ Edit"), id="edit_btn", state=CreateTaskDlg.title),
            Button(
                Const("❌ Cancel"),
                id="cancel_btn",
                on_click=on_cancel_to_menu,
                when="no_category",
            ),
            Cancel(Const("❌ Cancel"), show_mode=ShowMode.EDIT, when="has_category"),
        ),
        getter=[form_getter, default_category_getter],
        state=CreateTaskDlg.confirm,
    )


# --- Shared windows factory ---
def task_form_windows(confirm_handler):
    return [
        ask_title(),
        select_categories_window(),
        ask_description(),
        ask_due_date(),
        confirm(confirm_handler),
    ]


# --- Getters ---
async def form_getter(dialog_manager: DialogManager, **kwargs):
    selected_names = dialog_manager.dialog_data.get("category_names", "—")
    if isinstance(selected_names, list):
        selected_names = ", ".join(selected_names) if selected_names else "—"
    return {
        "title": dialog_manager.dialog_data.get("title", "—"),
        "categories": selected_names,
        "description": dialog_manager.dialog_data.get("description", "—"),
        "due_at": dialog_manager.dialog_data.get("due_at_str", "—"),
    }


async def default_category_getter(dialog_manager: DialogManager, **kwargs):
    if not isinstance(dialog_manager.start_data, dict):
        return {"has_category": False, "no_category": True}
    category_id, category_name = itemgetter("category_id", "category_name")(
        dialog_manager.start_data
    )
    return {
        "category_id": category_id,
        "category_name": category_name,
        "has_category": True,
        "no_category": False,
    }


async def get_categories_from_api(dialog_manager, **kwargs) -> dict:
    api_token = dialog_manager.middleware_data.get("api_token", "")
    tg_user_id = (
        dialog_manager.event.from_user.id if dialog_manager.event.from_user else None
    )
    category_service = CategoryService(api_token=api_token)
    data = await category_service.get_categories(
        user_id=str(tg_user_id), page=1, page_size=1000
    )

    items = data.get("results", []) or []

    cache = dialog_manager.dialog_data.get("items_cache", {})
    cache.update({it["id"]: it["name"] for it in items})
    dialog_manager.dialog_data["items_cache"] = cache
    return {"categories": items}


# --- Handlers ---
async def on_title_input(
    message: types.Message,
    widget: ManagedTextInput,
    manager: DialogManager,
    text: str,
) -> None:
    title = (text or "").strip()

    if not title:
        await message.answer("⚠️ Title can't be empty. Please send a title or /cancel.")
        return
    if len(title) > 255:
        await message.answer("⚠️ Title is too long (max 255 chars). Try a shorter one.")
        return

    manager.dialog_data["title"] = title
    await manager.next()


async def on_title_error(message: types.Message, *_):
    await message.answer("⚠️ Please send plain text for the title.")


async def on_categories_chosen(c: types.CallbackQuery, b: Button, m: DialogManager):
    cat_select = m.find("cat_select")
    if not cat_select:
        await c.answer("⚠️ No categories selected")
        return
    selected_ids = cat_select.get_checked()
    if not selected_ids:
        await c.answer("⚠️ Please choose at least one category")
        return
    selected_cat_names = m.dialog_data.get("items_cache", {})
    selected_names = [selected_cat_names.get(int(cid), "—") for cid in selected_ids]

    m.dialog_data["category_ids"] = selected_ids
    m.dialog_data["category_names"] = selected_names
    await m.switch_to(CreateTaskDlg.description)


async def on_create_confirm(callback, b, manager: DialogManager):
    title: str = manager.dialog_data.get("title", "").strip()
    description: str = manager.dialog_data.get("description", "").strip()
    due_at = manager.dialog_data.get("due_at")
    category_ids = manager.dialog_data.get("category_ids", [])

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
    task_dto = TaskDTO(
        title=title,
        category_ids=category_ids,
        description=description,
        due_at=due_at,
        tg=tg_dto,
    )
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


async def on_edit_confirm(c, b, m: DialogManager):
    name = m.dialog_data["name"]
    print(m.start_data)
    t_id = "Unknown"
    if isinstance(m.start_data, dict):
        t_id = m.start_data["id"]
    # call API → PUT/PATCH
    await c.answer(f"Updated task {t_id} → {name}")
    await m.done()


async def on_cancel_to_menu(
    callback: types.CallbackQuery, button: Button, manager: DialogManager
):
    await callback.answer("❌ Cancelled")
    await manager.start(
        MenuDlg.main, mode=StartMode.RESET_STACK, show_mode=ShowMode.DELETE_AND_SEND
    )


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
        manager.dialog_data["due_at_str"] = due.strftime("%Y-%m-%d %H:%M")
        await manager.next()
    except ValueError:
        await message.answer(
            "⚠️ Invalid format. Please send date & time in format: YYYY-MM-DD HH:MM"
        )


async def on_due_date_error(message: types.Message, *_):
    await message.answer("⚠️ Please send the due date in the correct format.")
