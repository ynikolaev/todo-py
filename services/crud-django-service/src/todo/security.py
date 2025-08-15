import hashlib
import hmac
import time

from django.conf import settings
from django.core.cache import cache
from rest_framework.exceptions import AuthenticationFailed


# Hash-Based Message Authentication Code (HMAC) Signing is an access token method
# that adds another level of security by forcing the requesting client
def verify_hmac(request):
    ts = request.headers.get("X-Bot-Timestamp")
    nonce = request.headers.get("X-Bot-Nonce")
    sig = request.headers.get("X-Bot-Signature")
    if not (ts and nonce and sig):
        raise AuthenticationFailed("Missing HMAC headers")

    # check freshness
    now = int(time.time())
    try:
        ts = int(ts)
    except ValueError as err:
        raise AuthenticationFailed("HMAC: bad timestamp") from err
    if abs(now - ts) > 300:  # allow 5 min skew while debugging
        raise AuthenticationFailed("HMAC: stale")

    # replay protection (120s window)
    cache_key = f"bot_hmac:{ts}:{nonce}"
    if cache.get(cache_key):
        raise AuthenticationFailed("Replay detected")
    cache.set(cache_key, 1, timeout=180)

    body = request.body or b""
    body_hash = hashlib.sha256(body).hexdigest()
    path = request.get_full_path()
    msg = f"{ts}.{request.method}.{path}.{body_hash}".encode()
    mac = hmac.new(settings.BOT_SHARED_SECRET.encode(), msg, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(mac, sig):
        raise AuthenticationFailed(
            f"HMAC: bad signature (server msg='{ts}.{request.method}.{path}.{body_hash}')"
        )
