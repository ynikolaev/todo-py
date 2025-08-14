# app/infra/db.py (minimal)
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.infra.config import settings

engine = create_async_engine(str(settings.DATABASE_URL), echo=False)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False)


@asynccontextmanager
async def session_scope():
    session: AsyncSession = SessionLocal()
    try:
        yield session
        await session.commit()
    except:
        await session.rollback()
        raise
    finally:
        await session.close()
