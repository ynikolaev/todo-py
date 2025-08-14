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
API_BASE = settings.DJANGO_API_BASE
BOT_SHARED_SECRET = settings.TELEGRAM_BOT_SHARED_SECRET.get_secret_value()
LONG_ACCESS_TOKEN = settings.SERVICE_REFRESH_TOKEN


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
            "Content-Type": "application/json",
            "Authorization": f"Bearer {LONG_ACCESS_TOKEN}",
            **sig_headers,
        }
    )


@asynccontextmanager
async def api_client() -> AsyncIterator[httpx.AsyncClient]:
    async with httpx.AsyncClient(
        base_url=str(API_BASE),
        timeout=DEFAULT_TIMEOUT,
        event_hooks={"request": [sign_request]},
    ) as client:
        yield client
