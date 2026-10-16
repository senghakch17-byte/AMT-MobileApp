import hashlib
import os

from slowapi import Limiter
from slowapi.util import get_remote_address
from starlette.requests import Request

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379")


def user_or_ip_key(request: Request) -> str:
    auth = request.headers.get("authorization")
    if auth:
        return "u:" + hashlib.sha256(auth.encode()).hexdigest()[:32]
    return get_remote_address(request)


limiter = Limiter(
    key_func=user_or_ip_key,
    storage_uri=f"{REDIS_URL}/1",  # keep rate-limit counters separate from cache DB 0
    swallow_errors=True,
    in_memory_fallback_enabled=True,
)