from fastapi import APIRouter

from app.api import announcements

api_router = APIRouter()
api_router.include_router(announcements.router)