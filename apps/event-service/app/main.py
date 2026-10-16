from contextlib import asynccontextmanager
from typing import AsyncGenerator
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded


from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.router import api_router
from app.core.config import settings
from app.database.session import close_db_connection, init_db_connection
from app.utils.storage import ensure_upload_dirs
from app.core.cache import redis_client
from app.core.limiter import limiter

ensure_upload_dirs()  # must exist before StaticFiles is mounted

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    # Startup
    await init_db_connection()
    yield
    await redis_client.aclose()
    # Shutdown
    await close_db_connection()


app = FastAPI(
    title=settings.PROJECT_NAME,
    lifespan=lifespan,
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Include API v1 Router
app.include_router(api_router)
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")


@app.get("/", include_in_schema=False)
async def root():
    return {"message": f"Welcome to {settings.PROJECT_NAME}. Visit /docs for API documentation."}