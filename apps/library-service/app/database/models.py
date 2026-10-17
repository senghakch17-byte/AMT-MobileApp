from datetime import datetime

from beanie import Document, PydanticObjectId
from pydantic import Field
from pymongo import IndexModel

from app.schemas.book import BookBase
from app.schemas.room import RoomBase
from app.utils.enums import BookingStatus
from app.utils.helpers import utcnow


class Room(RoomBase, Document):
    created_by: str
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "rooms"
        indexes = [
            IndexModel([("name", 1)], unique=True),
            [("is_active", 1)],
        ]


class Booking(Document):
    room_id: PydanticObjectId
    room_name: str  # snapshot, so history still reads correctly if the room is renamed
    user_id: str
    user_email: str
    start_at: datetime
    end_at: datetime
    attendees: int = 1
    purpose: str
    status: BookingStatus = BookingStatus.PENDING
    decided_by: str | None = None
    decided_at: datetime | None = None
    admin_note: str | None = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "bookings"
        indexes = [
            [("room_id", 1), ("status", 1), ("start_at", 1)],  # overlap checks / availability
            [("user_id", 1), ("start_at", -1)],                # "my bookings"
            [("status", 1), ("created_at", -1)],               # admin approval queue
            [("start_at", -1)],                                # admin history
        ]


class Book(BookBase, Document):
    created_by: str
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "books"
        indexes = [
            # unique only when an ISBN is present, so books without one don't collide
            IndexModel(
                [("isbn", 1)], unique=True, partialFilterExpression={"isbn": {"$type": "string"}}
            ),
            [("category", 1)],
            [("title", 1)],
        ]
