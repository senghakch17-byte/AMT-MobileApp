from fastapi import APIRouter

from app.api import bookings, rooms

api_router = APIRouter()
api_router.include_router(rooms.router)
api_router.include_router(bookings.router)
