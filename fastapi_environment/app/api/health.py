from fastapi import APIRouter

from app.core.config import settings
from app.schemas.msg import HealthCheck

router = APIRouter()


@router.get(
    "/health", response_model=HealthCheck, summary="Perform System Health Check"
)
async def check_health() -> HealthCheck:
    return HealthCheck(
        status="ok",
        environment=settings.ENVIRONMENT,
    )