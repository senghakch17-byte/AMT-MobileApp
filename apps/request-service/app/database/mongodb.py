from beanie import init_beanie
from pymongo import AsyncMongoClient
from pymongo.errors import ServerSelectionTimeoutError

from app.core.config import settings
from app.database.models import LeaveRequest, PreScholarshipRegistration

client: AsyncMongoClient | None = None


async def init_db() -> None:
    global client
    client = AsyncMongoClient(
        settings.MONGODB_URI,
        tz_aware=True,
        serverSelectionTimeoutMS=settings.MONGODB_SERVER_SELECTION_TIMEOUT_MS,
    )
    try:
        await client.admin.command("ping")
        await init_beanie(
            database=client[settings.MONGODB_DB_NAME],
            document_models=[LeaveRequest, PreScholarshipRegistration],
        )
    except ServerSelectionTimeoutError as exc:
        await client.close()
        client = None
        raise RuntimeError(
            "Could not reach MongoDB before the server selection timeout "
            f"({settings.MONGODB_SERVER_SELECTION_TIMEOUT_MS} ms). Check the "
            "MongoDB URI, DNS/network access, and (for Atlas) the deployment "
            "IP allowlist. Set MONGODB_SERVER_SELECTION_TIMEOUT_MS to adjust "
            "the wait."
        ) from exc
    

async def close_db() -> None:
    if client is not None:
        await client.close()

