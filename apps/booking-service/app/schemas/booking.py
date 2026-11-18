from datetime import datetime

from beanie import PydanticObjectId
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.utils.enums import BookingStatus
from app.utils.helpers import to_utc


class BookingCreate(BaseModel):
    room_id: PydanticObjectId
    start_at: datetime
    end_at: datetime
    attendees: int = Field(default=1, ge=1, le=500)
    purpose: str = Field(min_length=3, max_length=500)

    @field_validator("start_at", "end_at")
    @classmethod
    def normalize_tz(cls, value: datetime) -> datetime:
        return to_utc(value)  # naive input is treated as UTC

    @model_validator(mode="after")
    def check_times(self):
        if self.end_at <= self.start_at:
            raise ValueError("end_at must be after start_at")
        return self


class BookingDecision(BaseModel):
    """Optional note an admin attaches when approving or rejecting."""

    note: str | None = Field(default=None, max_length=500)


class BookingResponse(BaseModel):
    id: PydanticObjectId
    room_id: PydanticObjectId
    room_name: str
    user_id: str
    user_email: str
    start_at: datetime
    end_at: datetime
    attendees: int
    purpose: str
    status: BookingStatus
    decided_by: str | None = None
    decided_at: datetime | None = None
    admin_note: str | None = None
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)
