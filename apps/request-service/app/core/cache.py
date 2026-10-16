import json
import os
from collections.abc import Awaitable, Callable

from redis.asyncio import Redis
from redis.exceptions import RedisError

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379")
redis_client = Redis.from_url(f"{REDIS_URL}/0", decode_responses=True)

TTL_SECONDS = 60


def _ver_key(ns: str, user_id: str) -> str:
    return f"ver:{ns}:{user_id}"


async def bump_version(ns: str, user_id: str) -> None:
    """Invalidate every cached list for this user in this namespace."""
    try:
        await redis_client.incr(_ver_key(ns, user_id))
    except RedisError:
        pass  # fail open: the TTL will expire stale entries


async def cached_list(
    ns: str,
    user_id: str,
    suffix: str,
    loader: Callable[[], Awaitable[list[dict]]],
    ttl: int = TTL_SECONDS,
) -> list[dict]:
    key = None
    try:
        ver = await redis_client.get(_ver_key(ns, user_id)) or "0"
        key = f"cache:{ns}:{user_id}:v{ver}:{suffix}"
        hit = await redis_client.get(key)
        if hit is not None:
            return json.loads(hit)
    except RedisError:
        key = None  # Redis down -> go straight to Mongo

    data = await loader()

    if key:
        try:
            await redis_client.set(key, json.dumps(data), ex=ttl)
        except RedisError:
            pass
    return data