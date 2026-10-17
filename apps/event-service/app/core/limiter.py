from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.config import settings

limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=f"{settings.REDIS_URL}/1",  # separate DB from the cache
    swallow_errors=True,                    # don't 500 if Redis is down
    in_memory_fallback_enabled=True,
)