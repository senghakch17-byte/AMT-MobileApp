from fastapi import APIRouter

from app.api import bookings, books, rooms

api_router = APIRouter()
api_router.include_router(rooms.router)
api_router.include_router(bookings.router)
api_router.include_router(books.router)
