import asyncio

from sqlalchemy import text

from app.infra.config import settings
from app.infra.db import engine
from app.infra.logging import setup_logging


async def _db_ping() -> None:
    async with engine.begin() as conn:
        val = await conn.scalar(text("SELECT 1"))
        print("DB ping:", val)


def main() -> None:
    setup_logging(settings.LOG_LEVEL)
    print("Env:", settings.APP_ENV)
    print("DB URL:", settings.DATABASE_URL)
    # Run an async check
    asyncio.run(_db_ping())


if __name__ == "__main__":
    main()
