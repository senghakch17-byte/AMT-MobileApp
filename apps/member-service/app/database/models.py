from datetime import datetime

from beanie import Document
from pydantic import Field
from pymongo import IndexModel

from app.schemas.member import MemberBase
from app.utils.enums import DocumentType
from app.utils.helpers import utcnow


class Member(MemberBase, Document):
    """Profile of a user from the auth service, created on first access."""

    user_id: str  # `id` claim from the JWT issued by the auth service
    email: str
    role: str
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "members"
        indexes = [
            IndexModel([("user_id", 1)], unique=True),
            [("email", 1)],
            [("created_at", -1)],
        ]


class MemberDocument(Document):
    """A document a member has submitted. The file lives in private storage."""

    user_id: str
    title: str
    doc_type: DocumentType = DocumentType.OTHER
    description: str | None = None
    original_filename: str
    stored_filename: str  # server-generated name inside the document directory
    content_type: str
    size_bytes: int
    document_date: datetime | None = None  # stored as midnight UTC; exposed as a date
    uploaded_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "member_documents"
        indexes = [
            [("user_id", 1), ("uploaded_at", -1)],
            [("user_id", 1), ("doc_type", 1)],
        ]
