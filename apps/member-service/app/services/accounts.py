import asyncio
import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from fastapi import HTTPException, status

from app.core.config import settings


async def account_request(method: str, path: str, payload: dict) -> dict:
    if not settings.REGISTRATION_SERVICE_URL or not settings.INTERNAL_API_KEY:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "Account service integration is not configured")

    def send() -> dict:
        request = Request(
            f"{settings.REGISTRATION_SERVICE_URL.rstrip('/')}{path}",
            data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json", "x-internal-api-key": settings.INTERNAL_API_KEY},
            method=method,
        )
        with urlopen(request, timeout=5) as response:
            return json.loads(response.read())

    try:
        return await asyncio.to_thread(send)
    except HTTPError as error:
        raise HTTPException(error.code, "Account service rejected the request") from error
    except (OSError, URLError) as error:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "Account service is unavailable") from error
