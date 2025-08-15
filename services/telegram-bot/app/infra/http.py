from __future__ import annotations

import hashlib
import hmac
import os
import time
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import httpx

from app.infra.config import settings

DEFAULT_TIMEOUT = httpx.Timeout(10.0, connect=5.0)
API_BASE = str(settings.DJANGO_API_BASE).rstrip("/")
TOKEN_URL = f"{API_BASE}/api/token/"
REFRESH_URL = f"{API_BASE}/api/token/refresh/"
BOT_SHARED_SECRET = settings.TELEGRAM_BOT_SHARED_SECRET.get_secret_value()


def sign(body_bytes: bytes, method: str, path: str):
    ts = str(int(time.time()))
    nonce = os.urandom(12).hex()
    body_hash = hashlib.sha256(body_bytes).hexdigest()
    msg = f"{ts}.{method}.{path}.{body_hash}".encode()
    sig = hmac.new(BOT_SHARED_SECRET.encode(), msg, hashlib.sha256).hexdigest()
    return {
        "X-Bot-Timestamp": ts,
        "X-Bot-Nonce": nonce,
        "X-Bot-Signature": sig,
    }


async def sign_request(request: httpx.Request):
    body_bytes = request.content or b""
    sig_headers = sign(body_bytes, request.method.upper(), request.url.path)
    request.headers.update(
        {
            **sig_headers,
        }
    )


@asynccontextmanager
async def api_client(api_token: str) -> AsyncIterator[httpx.AsyncClient]:
    auth_header = {"Authorization": f"Bearer {api_token}"} if api_token else {}
    async with httpx.AsyncClient(
        base_url=API_BASE,
        timeout=DEFAULT_TIMEOUT,
        headers={
            **auth_header,
            "Accept": "application/json",
            "User-Agent": "TaskerBot/1.0",
            "Content-Type": "application/json",
        },
        event_hooks={"request": [sign_request]},
    ) as client:
        yield client
