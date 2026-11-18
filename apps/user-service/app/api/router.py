from fastapi import APIRouter

from app.api import documents, users

api_router = APIRouter()
api_router.include_router(users.router)
api_router.include_router(documents.router)
