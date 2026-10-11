from datetime import datetime, timezone

from beanie import PydanticObjectId
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.utils.enums import EventCategory, EventStatus


def _to_utc(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value.astimezone(timezone.utc)


class EventBase(BaseModel):
    title: str = Field(min_length=3, max_length=150)
    description: str = Field(min_length=10, max_length=5000)
    category: EventCategory = EventCategory.ANNOUNCEMENT
    location: str = Field(min_length=2, max_length=200)
    start_at: datetime
    end_at: datetime | None = None
    status: EventStatus = EventStatus.DRAFT

    @field_validator("start_at", "end_at")
    @classmethod
    def normalize_tz(cls, value: datetime | None) -> datetime | None:
        return _to_utc(value)

    @model_validator(mode="after")
    def check_dates(self):
        if self.end_at and self.end_at < self.start_at:
            raise ValueError("end_at must be on or after start_at")
        return self


class EventCreate(EventBase):
    pass


class EventUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=3, max_length=150)
    description: str | None = Field(default=None, min_length=10, max_length=5000)
    category: EventCategory | None = None
    location: str | None = Field(default=None, min_length=2, max_length=200)
    start_at: datetime | None = None
    end_at: datetime | None = None
    status: EventStatus | None = None


class EventResponse(EventBase):
    id: PydanticObjectId
    images: list[str] = []
    created_by: str
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)
