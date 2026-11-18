from datetime import datetime

from beanie import PydanticObjectId
from pydantic import BaseModel, ConfigDict, Field, field_validator


class RoomBase(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    description: str | None = Field(default=None, max_length=1000)
    location: str = Field(min_length=2, max_length=200, description="Floor / wing / area")
    capacity: int = Field(ge=1, le=500)
    amenities: list[str] = Field(default_factory=list, max_length=30)
    is_active: bool = True  # inactive rooms are hidden from users and cannot be booked

    @field_validator("name", "location")
    @classmethod
    def strip_text(cls, value: str) -> str:
        return value.strip()

    @field_validator("amenities")
    @classmethod
    def clean_amenities(cls, value: list[str]) -> list[str]:
        cleaned = [a.strip() for a in value if a and a.strip()]
        if any(len(a) > 50 for a in cleaned):
            raise ValueError("each amenity must be at most 50 characters")
        return list(dict.fromkeys(cleaned))  # drop duplicates, keep order


class RoomCreate(RoomBase):
    pass


class RoomUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=100)
    description: str | None = Field(default=None, max_length=1000)
    location: str | None = Field(default=None, min_length=2, max_length=200)
    capacity: int | None = Field(default=None, ge=1, le=500)
    amenities: list[str] | None = Field(default=None, max_length=30)
    is_active: bool | None = None


class RoomResponse(RoomBase):
    id: PydanticObjectId
    created_by: str
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class BusySlot(BaseModel):
    """An approved booking, shown without any user details."""

    start_at: datetime
    end_at: datetime
