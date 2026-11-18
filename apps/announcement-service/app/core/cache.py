import logging

from redis.asyncio import Redis, from_url
from redis.exceptions import RedisError

from app.core.config import settings

logger = logging.getLogger(__name__)

redis_client: Redis = from_url(f"{settings.REDIS_URL}/0", decode_responses=True)
LIST_VERSION_KEY = "announcements:list:version"


# All helpers fail open: if Redis is down, the API falls back to MongoDB.
async def cache_get(key: str) -> str | None:
    try:
        return await redis_client.get(key)
    except RedisError:
        logger.warning("Redis GET failed", exc_info=True)
        return None


async def cache_set(key: str, value: str | bytes, ttl: int) -> None:
    try:
        await redis_client.set(key, value, ex=ttl)
    except RedisError:
        logger.warning("Redis SET failed", exc_info=True)


async def get_list_version() -> str:
    try:
        return await redis_client.get(LIST_VERSION_KEY) or "0"
    except RedisError:
        return "0"


async def invalidate_announcement(announcement_id: object | None = None) -> None:
    """Bump list version (orphans every cached list page) and drop detail keys."""
    try:
        await redis_client.incr(LIST_VERSION_KEY)
        if announcement_id is not None:
            await redis_client.delete(
                f"announcements:detail:admin:{announcement_id}", f"announcements:detail:public:{announcement_id}"
            )
    except RedisError:
        logger.warning("Redis invalidation failed", exc_info=True)
