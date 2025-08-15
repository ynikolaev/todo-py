import asyncio
import base64
import json
import logging
import time

import httpx
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from redis.asyncio import Redis

from app.infra.config import settings

logger = logging.getLogger(__name__)

# Django API settings
API_BASE = str(settings.DJANGO_API_BASE).rstrip("/")
TOKEN_URL = f"{API_BASE}/api/token"
REFRESH_URL = f"{API_BASE}/api/token/refresh"
BOT_USERNAME = settings.TELEGRAM_BOT_SERVICE_USERNAME
BOT_PASSWORD = settings.TELEGRAM_BOT_SERVICE_PASSWORD.get_secret_value()
REDIS_DSN = f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/0"

ACCESS_KEY = "jwt:bot:access"
REFRESH_KEY = "jwt:bot:refresh"


def _get_exp(token: str) -> float | None:
    """Decode JWT to extract exp timestamp."""
    try:
        _, payload, _ = token.split(".")
        payload += "==="[: (4 - len(payload) % 4) % 4]
        data = json.loads(base64.urlsafe_b64decode(payload))
        return float(data.get("exp"))
    except Exception:
        return None


class DjangoAuthMiddleware(BaseMiddleware):
    def __init__(self):
        super().__init__()
        self._lock = asyncio.Lock()

    async def get_access_token(self) -> str:
        """Public helper for boot self-test."""
        redis = Redis.from_url(REDIS_DSN)
        try:
            return await self._ensure_access_token(redis)  # reuse your internal logic
        finally:
            await redis.aclose()

    async def _get_token_from_api(self) -> tuple[str, str]:
        async with httpx.AsyncClient(timeout=5.0) as client:
            r = await client.post(
                TOKEN_URL, json={"username": BOT_USERNAME, "password": BOT_PASSWORD}
            )
            r.raise_for_status()
            data = r.json()
            logger.info("Obtained new refresh token: %s", data["refresh"])
            logger.info("Obtained new access token: %s", data["access"])
            return data["access"], data["refresh"]

    async def _refresh_access_token(self, refresh: str) -> str | None:
        async with httpx.AsyncClient(timeout=5.0) as client:
            r = await client.post(REFRESH_URL, json={"refresh": refresh})
            if r.status_code != 200:
                return None
            return r.json()["access"]

    async def _ensure_access_token(self, redis: Redis) -> str:
        # Try existing access
        raw = await redis.get(ACCESS_KEY)
        if raw:
            token = raw.decode()
            exp = _get_exp(token)
            if exp and exp - time.time() > 30:  # 30s leeway
                return token

        # Acquire lock to prevent race
        async with self._lock:
            raw = await redis.get(ACCESS_KEY)
            if raw:
                token = raw.decode()
                exp = _get_exp(token)
                if exp and exp - time.time() > 30:
                    return token

            # Try refresh
            refresh_token = await redis.get(REFRESH_KEY)
            if refresh_token:
                new_access = await self._refresh_access_token(refresh_token.decode())
                if new_access:
                    await redis.set(ACCESS_KEY, new_access, ex=300)  # ~5m
                    return new_access

            # Full login
            access, refresh = await self._get_token_from_api()
            await redis.set(ACCESS_KEY, access, ex=300)
            await redis.set(REFRESH_KEY, refresh)
            return access

    async def __call__(self, handler, event: TelegramObject, data: dict):
        redis = Redis.from_url(REDIS_DSN)
        try:
            token = await self._ensure_access_token(redis)
            data["api_token"] = token  # handlers can read this
            return await handler(event, data)
        finally:
            await redis.aclose()
