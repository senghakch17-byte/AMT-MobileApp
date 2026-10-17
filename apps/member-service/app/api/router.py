from fastapi import APIRouter

from app.api import documents, members

api_router = APIRouter()
api_router.include_router(members.router)
api_router.include_router(documents.router)
