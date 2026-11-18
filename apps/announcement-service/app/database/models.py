from datetime import datetime

from beanie import Document
from pydantic import Field

from app.schemas.announcement import AnnouncementBase
from app.utils.helpers import utcnow


class Announcement(AnnouncementBase, Document):
    images: list[str] = []  # first image is the cover
    created_by: str
    created_by_email: str
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "announcements"
        indexes = [
            [("status", 1), ("start_at", -1)],
            [("category", 1)],
        ]