import os
import httpx

API_BASE = os.getenv("API_BASE", "http://crud-django-service:8000/api")
BOT_SHARED_SECRET = os.getenv("BOT_SHARED_SECRET", "devsecret")


class ApiClient:
    def __init__(self):
        self.tokens = {}  # telegram_id -> token (can be swapped to Redis)

    async def ensure_token(self, telegram_id: int, username: str):
        if telegram_id in self.tokens:
            return self.tokens[telegram_id]
        async with httpx.AsyncClient() as c:
            r = await c.post(
                f"{API_BASE.rstrip('/').replace('/api','')}/api/auth/telegram/",
                headers={"X-Bot-Secret": BOT_SHARED_SECRET},
                json={"telegram_id": telegram_id, "username": username},
                timeout=10,
            )
        r.raise_for_status()
        token = r.json()["token"]
        self.tokens[telegram_id] = token
        return token

    async def list_tasks(self, telegram_id: int, username: str):
        token = await self.ensure_token(telegram_id, username)
        async with httpx.AsyncClient() as c:
            r = await c.get(
                f"{API_BASE}/tasks/", headers={"Authorization": f"Token {token}"}
            )
        r.raise_for_status()
        return r.json()

    async def create_task(self, telegram_id: int, username: str, payload: dict):
        token = await self.ensure_token(telegram_id, username)
        async with httpx.AsyncClient() as c:
            r = await c.post(
                f"{API_BASE}/tasks/",
                headers={"Authorization": f"Token {token}"},
                json=payload,
            )
        r.raise_for_status()
        return r.json()
