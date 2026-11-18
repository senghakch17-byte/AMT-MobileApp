import asyncio
import json
from urllib.error import URLError
from urllib.request import Request, urlopen

from app.core.config import settings
from app.utils.logger import logger


async def publish_notification(notification: dict) -> None:
    if not settings.NOTIFICATION_SERVICE_URL or not settings.INTERNAL_API_KEY:
        logger.warning("Notification skipped: producer configuration is missing")
        return

    def send() -> None:
        request = Request(
            f"{settings.NOTIFICATION_SERVICE_URL.rstrip('/')}/internal/events",
            data=json.dumps(notification).encode(),
            headers={"Content-Type": "application/json", "x-internal-api-key": settings.INTERNAL_API_KEY},
            method="POST",
        )
        with urlopen(request, timeout=3):
            pass

    try:
        await asyncio.to_thread(send)
    except (OSError, URLError) as error:
        logger.warning("Notification was not queued: %s", error)
