from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI

from app.api.router import api_router
from app.core.config import settings
from app.database.session import close_db_connection, init_db_connection
from app.schemas.msg import HealthCheck
from app.utils.storage import ensure_upload_dirs


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    # Startup
    ensure_upload_dirs()
    await init_db_connection()
    yield
    # Shutdown
    await close_db_connection()


app = FastAPI(
    title=settings.PROJECT_NAME,
    lifespan=lifespan,
    root_path=settings.ROOT_PATH,
)

# Include API v1 Router
# (no StaticFiles mount: member documents are private and served by authenticated endpoints)
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/health", response_model=HealthCheck, tags=["Health"])
async def health():
    return HealthCheck(status="ok", environment=settings.ENVIRONMENT)


@app.get("/", include_in_schema=False)
async def root():
    return {"message": f"Welcome to {settings.PROJECT_NAME}. Visit /docs for API documentation."}
