from beanie import init_beanie
from pymongo import AsyncMongoClient

from app.core.config import settings
from app.database.models import Member, MemberDocument

client: AsyncMongoClient | None = None


async def init_db() -> None:
    global client
    client = AsyncMongoClient(
        settings.MONGODB_URI, tz_aware=True, serverSelectionTimeoutMS=5000
    )
    await client.admin.command("ping")  # fail at startup if Mongo is unreachable
    await init_beanie(
        database=client[settings.MONGODB_DB_NAME],
        document_models=[Member, MemberDocument],
    )


async def close_db() -> None:
    if client is not None:
        await client.close()
