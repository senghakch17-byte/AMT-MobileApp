from datetime import datetime

from pydantic import BaseModel, Field

from app.utils.enums import RequestStatus
from app.utils.helpers import utcnow


class RequestMeta(BaseModel):
    """Server-managed fields shared by every request type (never sent by the client)."""

    student_id: str
    student_email: str
    status: RequestStatus = RequestStatus.PENDING
    reviewed_by: str | None = None
    review_comment: str | None = None
    reviewed_at: datetime | None = None
    cancelled_at: datetime | None = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)