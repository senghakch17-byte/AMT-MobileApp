from datetime import date, datetime

from beanie import PydanticObjectId
from pydantic import BaseModel, ConfigDict

from app.utils.enums import DocumentType


class DocumentResponse(BaseModel):
    id: PydanticObjectId
    user_id: str
    title: str
    doc_type: DocumentType
    description: str | None = None
    original_filename: str
    content_type: str
    size_bytes: int
    document_date: date | None = None  # when the document was issued / dated
    uploaded_at: datetime
    download_url: str  # authenticated endpoint; files are never served statically
    model_config = ConfigDict(from_attributes=True)
