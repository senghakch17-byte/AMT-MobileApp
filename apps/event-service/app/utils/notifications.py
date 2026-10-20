import asyncio
import json
from urllib.error import URLError
from urllib.request import Request, urlopen

from app.core.config import settings
from app.utils.logger import logger


async def publish_notification(event: dict) -> None:
    if not settings.NOTIFICATION_SERVICE_URL or not settings.INTERNAL_API_KEY:
        logger.warning("Notification event skipped: producer configuration is missing")
        return

    def send() -> None:
        request = Request(
            f"{settings.NOTIFICATION_SERVICE_URL.rstrip('/')}/api/v1/internal/events",
            data=json.dumps(event).encode(),
            headers={"Content-Type": "application/json", "x-internal-api-key": settings.INTERNAL_API_KEY},
            method="POST",
        )
        with urlopen(request, timeout=3):
            pass

    try:
        await asyncio.to_thread(send)
    except (OSError, URLError) as error:
        logger.warning("Notification event was not queued: %s", error)