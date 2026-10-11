from fastapi import APIRouter

from app.api import events

api_router = APIRouter()
api_router.include_router(events.router)