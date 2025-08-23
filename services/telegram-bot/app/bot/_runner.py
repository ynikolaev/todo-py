from __future__ import annotations

import asyncio
import importlib
import logging
import pkgutil
from contextlib import suppress

import httpx
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand
from aiogram_dialog import setup_dialogs

from app import dialogs
from app.infra.config import settings
from app.infra.logging import setup_logging
from app.middlewares.auth_middleware import DjangoAuthMiddleware


def load_all_modules(package):
    for _, name, _ in pkgutil.walk_packages(package.__path__, package.__name__ + "."):
        print(name)
        module = importlib.import_module(name)
        yield module


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
            BotCommand(command="main", description="👀 Show menu"),
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

    # Adding routers and dialogs
    for module in load_all_modules(dialogs):
        if hasattr(module, "router"):
            dp.include_router(module.router)
        if hasattr(module, "dialog"):
            dp.include_router(module.dialog)

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
