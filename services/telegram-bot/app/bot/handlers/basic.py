import textwrap

from aiogram import Router, types
from aiogram.filters import Command, CommandStart
from aiogram.types import Message

from app.infra.http import api_client

router = Router(name=__name__)


@router.message(CommandStart())
async def cmd_start(message: types.Message) -> None:
    user = message.from_user
    if not user:
        await message.answer("Hello! Please, set your Telegram profile name.")
        return
    name = user.full_name if user else "Stranger"
    async with api_client("") as client:
        resp = await client.get("/healthz")
    await message.answer(
        f"""Hello, {name}!\nI'm TaskerBot. Use /help to see what I can do.
        \nHealth check response: {resp.status_code} {resp.reason_phrase}""",
    )


@router.message(Command("help"))
async def cmd_help(message: types.Message) -> None:
    await message.answer(
        textwrap.dedent(
            """
            /start — greet the bot
            /selftest — test connection
            /help — this help
            /profile — set your profile name
            /about — version & env info
            /profile_dialog — set your profile name (dialog)
            """
        )
    )


@router.message(Command("selftest"))
async def selftest(message: Message, api_token: str):
    async with api_client(api_token) as client:
        r = await client.get("api/whoami")
    await message.answer(f"status={r.status_code} body={r.text[:120]}")


@router.message(Command("about"))
async def cmd_about(message: types.Message) -> None:
    from app.infra.config import settings

    if (
        not settings.DATABASE_URL.host
        or not settings.DATABASE_URL.port
        or not settings.DATABASE_URL.path
    ):
        await message.answer("Database URL is not configured properly.")
        return
    await message.answer(
        f"TaskerBot\n"
        f"Env: {settings.APP_ENV}\n"
        f"DB: {settings.DATABASE_URL.host}:{settings.DATABASE_URL.port} / {settings.DATABASE_URL.path.lstrip('/')}"
    )
