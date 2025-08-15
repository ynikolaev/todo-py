from collections.abc import Callable, Sequence
from typing import Any, TypeVar

from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram_dialog.widgets.kbd import Select
from aiogram_dialog.widgets.text import Text

TItem = TypeVar("TItem")


class VerticalSelect(Select[TItem]):
    def __init__(
        self,
        text: Text,
        id: str,
        item_id_getter: Callable[[TItem], str],
        items: str,
        **kwargs: Any,
    ):
        super().__init__(
            text=text, id=id, item_id_getter=item_id_getter, items=items, **kwargs
        )

    async def render_kbd(self, data, manager):
        # 1) resolve items from your getter
        items: Sequence[TItem] = self.items_getter(data)

        # 2) build one button per row
        kb = InlineKeyboardBuilder()
        for idx, item in enumerate(items, start=1):
            item_id = self.item_id_getter(item)
            # Render per-item text (again API may differ slightly)
            text = await self.text.render_text(
                {"item": item, "item_index": idx, **data}, manager
            )
            # Build callback data for this item (method name may differ)
            cb_data = self._item_callback_data(item_id)
            print(f"Adding button: {text} with callback {cb_data}")
            kb.row(InlineKeyboardButton(text=text, callback_data=cb_data), width=1)

        return kb.as_markup()
