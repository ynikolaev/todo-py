from aiogram import Router, types
from aiogram.filters import Command, CommandStart

router = Router(name=__name__)


@router.message(CommandStart())
async def cmd_start(message: types.Message) -> None:
    user = message.from_user
    name = user.full_name if user else "Stranger"
    await message.answer(
        f"Hello, {name}!\nI'm TaskerBot. Use /help to see what I can do."
    )


@router.message(Command("help"))
async def cmd_help(message: types.Message) -> None:
    await message.answer(
        "/start — greet the bot\n/help — this help\n/profile - set your profile name\n/about — version & env info"
    )


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
