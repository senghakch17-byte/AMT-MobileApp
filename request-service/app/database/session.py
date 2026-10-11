# Database abstraction layer

from app.database.mongodb import close_db, init_db
from app.utils.logger import logger


async def init_db_connection() -> None:
    """Initialize DB connection on application startup."""
    logger.info("Initializing database connection...")
    await init_db()


async def close_db_connection() -> None:
    """Close DB connections on application shutdown."""
    logger.info("Closing database connections...")
    await close_db()