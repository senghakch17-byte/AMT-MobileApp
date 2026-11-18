from enum import Enum


class AnnouncementStatus(str, Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    CANCELLED = "cancelled"


class AnnouncementCategory(str, Enum):
    SCHOLARSHIP = "scholarship"
    FUNDRAISING = "fundraising"
    WORKSHOP = "workshop"
    CEREMONY = "ceremony"
    ANNOUNCEMENT = "announcement"
    OTHER = "other"