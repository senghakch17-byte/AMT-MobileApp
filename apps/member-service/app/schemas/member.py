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
    active: bool = True
    deleted_at: datetime | None = None
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class AdminUserCreate(MemberBase):
    name: str = Field(min_length=2, max_length=120)
    email: str = Field(min_length=3, max_length=320)
    password: str = Field(min_length=8, max_length=128)
    mobile: str = Field(min_length=6, max_length=30)
    role: str = Field(default="user", pattern="^(user|admin)$")


class AdminUserUpdate(MemberUpdate):
    email: str | None = Field(default=None, min_length=3, max_length=320)
    mobile: str | None = Field(default=None, min_length=6, max_length=30)
    role: str | None = Field(default=None, pattern="^(user|admin)$")
    active: bool | None = None
