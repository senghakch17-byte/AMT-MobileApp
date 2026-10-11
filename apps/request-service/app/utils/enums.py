from enum import Enum


class RequestStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


class LeaveType(str, Enum):
    SICK = "sick"
    PERSONAL = "personal"
    FAMILY_EMERGENCY = "family_emergency"
    OTHER = "other"


class ScholarshipType(str, Enum):
    NEED_BASED = "need_based"
    MERIT = "merit"


class Gender(str, Enum):
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"