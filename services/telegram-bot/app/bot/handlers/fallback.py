# app/bot/handlers/fallback.py
from aiogram import F, Router, types

router = Router(name=__name__)


@router.message(F.text.startswith("/"))
async def unknown_command(message: types.Message) -> None:
    await message.answer("Unknown command. Try /help")
