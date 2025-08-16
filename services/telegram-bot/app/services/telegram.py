from aiogram import types
from pydantic import BaseModel


class TelegramAccountDTO(BaseModel):
    user_id: int
    chat_id: int
    tg_username: str | None = None

    @classmethod
    def from_callback(cls, callback: types.CallbackQuery) -> "TelegramAccountDTO":
        if not callback.message:
            raise ValueError(
                "CallbackQuery must have a message to extract TelegramAccountDTO"
            )
        return cls(
            user_id=callback.from_user.id,
            chat_id=callback.message.chat.id,
            tg_username=callback.from_user.username,
        )
