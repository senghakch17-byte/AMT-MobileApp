from datetime import date, datetime

from beanie import PydanticObjectId
from pydantic import BaseModel, ConfigDict, Field, field_validator

PHONE_PATTERN = r"^\+?[0-9 ()\-]{6,20}$"


class MemberBase(BaseModel):
    full_name: str | None = Field(default=None, min_length=2, max_length=120)
    phone: str | None = Field(default=None, pattern=PHONE_PATTERN)
    address: str | None = Field(default=None, min_length=2, max_length=300)
    date_of_birth: date | None = None

    @field_validator("date_of_birth")
    @classmethod
    def check_dob(cls, value: date | None) -> date | None:
        if value is not None and value > date.today():
            raise ValueError("date_of_birth cannot be in the future")
        return value


class MemberUpdate(MemberBase):
    """Self-service profile edit. Send only the fields to change; null clears a field."""


class MemberResponse(MemberBase):
    id: PydanticObjectId
    user_id: str
    email: str
    role: str
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)
