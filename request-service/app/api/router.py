from fastapi import APIRouter
from app.api import leave_requests, pre_scholarship
from app.api import health

api_router = APIRouter()
api_router.include_router(health.router, tags=["Health"])
api_router.include_router(leave_requests.router)
api_router.include_router(pre_scholarship.router)