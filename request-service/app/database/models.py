from beanie import Document

from app.schemas.common import RequestMeta
from app.schemas.leave_request import LeaveRequestBase
from app.schemas.pre_scholarship import PreScholarshipBase


class LeaveRequest(LeaveRequestBase, RequestMeta, Document):
    class Settings:
        name = "leave_requests"
        indexes = [
            [("student_id", 1), ("status", 1)],
            [("created_at", -1)],
        ]


class PreScholarshipRegistration(PreScholarshipBase, RequestMeta, Document):
    class Settings:
        name = "pre_scholarship_registrations"
        indexes = [
            [("student_id", 1), ("academic_year", 1)],
            [("status", 1), ("scholarship_type", 1)],
        ]