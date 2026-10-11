from datetime import date

from beanie import PydanticObjectId
from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.schemas.common import RequestMeta
from app.utils.enums import LeaveType


class LeaveRequestBase(BaseModel):  # also the body for "send request"
    leave_type: LeaveType
    start_date: date
    end_date: date
    reason: str = Field(min_length=10, max_length=500)
    attachment_urls: list[str] = []

    @model_validator(mode="after")
    def check_dates(self):
        if self.end_date < self.start_date:
            raise ValueError("end_date must be on or after start_date")
        return self


class LeaveRequestUpdate(BaseModel):
    leave_type: LeaveType | None = None
    start_date: date | None = None
    end_date: date | None = None
    reason: str | None = Field(default=None, min_length=10, max_length=500)
    attachment_urls: list[str] | None = None


class LeaveRequestResponse(LeaveRequestBase, RequestMeta):
    id: PydanticObjectId
    model_config = ConfigDict(from_attributes=True)