from enum import Enum


class EventStatus(str, Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    CANCELLED = "cancelled"


class EventCategory(str, Enum):
    SCHOLARSHIP = "scholarship"
    FUNDRAISING = "fundraising"
    WORKSHOP = "workshop"
    CEREMONY = "ceremony"
    ANNOUNCEMENT = "announcement"
    OTHER = "other"