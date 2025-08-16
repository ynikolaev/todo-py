from __future__ import annotations

import asyncio
import logging
from contextlib import suppress

import httpx
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand
from aiogram_dialog import setup_dialogs

from app.dialogs import (
    menu as menu_dialog,
    profile as profile_dialog,
)
from app.dialogs.categories import (
    create as categories_dialog,
    list_all as categories_list_dialog,
)
from app.dialogs.tasks import (
    create as create_tasks_dialog,
)
from app.infra.config import settings
from app.infra.logging import setup_logging
from app.middlewares.auth_middleware import DjangoAuthMiddleware

from .handlers import basic, fallback, profile


async def _auth_self_test(mw: DjangoAuthMiddleware) -> None:
    """
    1) Ensure we can obtain an access token via the middleware.
    2) Call a protected endpoint (/api/whoami) with it.
    Raises on failure so the process doesn’t start half-broken.
    """

    API_BASE = str(settings.DJANGO_API_BASE).rstrip("/")  # noqa: N806
    token = await mw.get_access_token()
    async with httpx.AsyncClient(timeout=5.0) as client:
        r = await client.get(
            f"{API_BASE}/api/whoami", headers={"Authorization": f"Bearer {token}"}
        )
        if r.status_code != 200:
            # Include response body for quick diagnosis
            raise RuntimeError(f"Auth self-test failed: {r.status_code} {r.text}")


async def _set_bot_commands(bot: Bot) -> None:
    await bot.set_my_commands(
        [
            BotCommand(command="list_categories", description="👀 Show categories"),
            BotCommand(command="new_task", description="🆕 Create a new task"),
            BotCommand(command="new_category", description="📂 Create a new category"),
            BotCommand(command="newtask", description="🔔 Create a new task"),
            BotCommand(command="help", description="ℹ️ How to use the bot"),
            # BotCommand(command="profile", description="Set your profile name"),
            # BotCommand(
            #     command="profile_dialog", description="Set your profile name (dialog)"
            # ),
            # BotCommand(command="about", description="About this bot"),
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
    auth_middleware = DjangoAuthMiddleware()
    dp.update.middleware(auth_middleware)

    if not getattr(settings, "SKIP_AUTH_SELF_TEST", False):
        await _auth_self_test(auth_middleware)

    setup_dialogs(dp)

    dp.include_router(basic.router)
    dp.include_router(profile.router)
    dp.include_router(profile_dialog.router)
    dp.include_router(profile_dialog.profile_dialog_window)
    dp.include_router(menu_dialog.menu_dialog)
    dp.include_router(categories_dialog.category_create_dialog_window)
    dp.include_router(categories_dialog.router)
    dp.include_router(categories_list_dialog.categories_list_dialog)
    dp.include_router(categories_list_dialog.router)
    dp.include_router(create_tasks_dialog.task_create_dialog_window)
    dp.include_router(create_tasks_dialog.router)
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
