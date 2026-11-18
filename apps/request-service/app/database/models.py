from beanie import Document

from app.schemas.common import RequestMeta
from app.schemas.leave_request import LeaveRequestBase


class LeaveRequest(LeaveRequestBase, RequestMeta, Document):
    class Settings:
        name = "leave_requests"
        indexes = [
            [("student_id", 1), ("status", 1)],
            [("created_at", -1)],
        ]
