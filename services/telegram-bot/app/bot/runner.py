from __future__ import annotations

import asyncio
import logging
from contextlib import suppress

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand
from aiogram_dialog import setup_dialogs

from app.dialogs import profile as profile_dialog
from app.infra.config import settings
from app.infra.logging import setup_logging

from .handlers import basic, fallback, profile


async def _set_bot_commands(bot: Bot) -> None:
    await bot.set_my_commands(
        [
            BotCommand(command="start", description="Start the bot"),
            BotCommand(command="help", description="How to use the bot"),
            BotCommand(command="profile", description="Set your profile name"),
            BotCommand(
                command="profile_dialog", description="Set your profile name (dialog)"
            ),
            BotCommand(command="about", description="About this bot"),
        ]
    )


async def run_polling() -> None:
    """
    Create Bot & Dispatcher, register routers, set commands, and run long polling.
    """
    setup_logging(settings.LOG_LEVEL)
    logging.getLogger(__name__).info("Starting TaskerBot (polling)…")

    if not settings.TELEGRAM_BOT_TOKEN:
        raise ValueError("TELEGRAM_BOT_TOKEN is not set in the environment")

    bot = Bot(
        token=settings.TELEGRAM_BOT_TOKEN.get_secret_value(),
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )

    dp = Dispatcher(storage=MemoryStorage())

    setup_dialogs(dp)

    dp.include_router(basic.router)
    dp.include_router(profile.router)
    dp.include_router(profile_dialog.router)
    dp.include_router(profile_dialog.profile_dialog_window)
    dp.include_router(fallback.router)

    # Set bot commands shown in Telegram’s UI
    await _set_bot_commands(bot)

    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        await bot.session.close()


def main() -> None:
    with suppress(KeyboardInterrupt):
        asyncio.run(run_polling())


if __name__ == "__main__":
    main()
