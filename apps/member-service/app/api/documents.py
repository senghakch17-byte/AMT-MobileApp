from datetime import date, datetime, timezone
from pathlib import Path

from beanie import PydanticObjectId
from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Query,
    Response,
    UploadFile,
    status,
)
from fastapi.responses import FileResponse

from app.api.deps import get_current_user, require_self_or_admin
from app.core.config import settings
from app.core.security import CurrentUser
from app.database.models import MemberDocument
from app.schemas.document import DocumentResponse
from app.utils.enums import DocumentType
from app.utils.storage import delete_document_file, document_path, save_document

router = APIRouter(prefix="/members", tags=["Member Documents"])


def _serialize(doc: MemberDocument) -> DocumentResponse:
    data = doc.model_dump(exclude={"stored_filename"})
    data["document_date"] = doc.document_date.date() if doc.document_date else None
    data["download_url"] = (
        f"{settings.PUBLIC_BASE_URL}{settings.API_V1_STR}"
        f"/members/{doc.user_id}/documents/{doc.id}/download"
    )
    return DocumentResponse.model_validate(data)


async def _history(
    response: Response, user_id: str, doc_type: DocumentType | None, skip: int, limit: int
) -> list[DocumentResponse]:
    conditions = [MemberDocument.user_id == user_id]
    if doc_type:
        conditions.append(MemberDocument.doc_type == doc_type)
    query = MemberDocument.find(*conditions)
    response.headers["X-Total-Count"] = str(await query.count())
    docs = await query.sort("-uploaded_at").skip(skip).limit(limit).to_list()
    return [_serialize(d) for d in docs]


async def _download(user_id: str, document_id: PydanticObjectId) -> FileResponse:
    doc = await MemberDocument.get(document_id)
    if doc is None or doc.user_id != user_id:  # never reveal a document under another member
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Document not found")
    path = document_path(doc.stored_filename)
    if not path.is_file():
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Document file is missing")
    return FileResponse(path, media_type=doc.content_type, filename=doc.original_filename)


# ---------- Any logged-in user: own documents ----------
# NOTE: "/me" routes are declared before "/{user_id}" so "me" is never read as an id.

@router.post(
    "/me/documents", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED
)
async def upload_my_document(
    file: UploadFile = File(..., description="PDF, JPEG, PNG or WEBP"),
    title: str = Form(..., min_length=2, max_length=150),
    doc_type: DocumentType = Form(DocumentType.OTHER),
    description: str | None = Form(None, max_length=1000),
    document_date: date | None = Form(None, description="Date the document was issued"),
    user: CurrentUser = Depends(get_current_user),
):
    if document_date and document_date > date.today():
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT, "document_date cannot be in the future"
        )
    stored = await save_document(file)
    doc = MemberDocument(
        user_id=user.id,
        title=title.strip(),
        doc_type=doc_type,
        description=description,
        original_filename=Path(file.filename or "document").name[:255],
        stored_filename=stored.stored_filename,
        content_type=stored.content_type,
        size_bytes=stored.size_bytes,
        document_date=(
            datetime(document_date.year, document_date.month, document_date.day, tzinfo=timezone.utc)
            if document_date
            else None
        ),
    )
    try:
        await doc.insert()
    except Exception:
        delete_document_file(stored.stored_filename)  # don't leave an orphan file behind
        raise
    return _serialize(doc)


@router.get("/me/documents", response_model=list[DocumentResponse])
async def list_my_documents(
    response: Response,
    doc_type: DocumentType | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    user: CurrentUser = Depends(get_current_user),
):
    return await _history(response, user.id, doc_type, skip, limit)


@router.get("/me/documents/{document_id}/download")
async def download_my_document(
    document_id: PydanticObjectId, user: CurrentUser = Depends(get_current_user)
):
    return await _download(user.id, document_id)


# ---------- Admin (any member) or the member themselves: view document history ----------

@router.get("/{user_id}/documents", response_model=list[DocumentResponse])
async def list_member_documents(
    response: Response,
    user_id: str,
    doc_type: DocumentType | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    _: CurrentUser = Depends(require_self_or_admin),
):
    return await _history(response, user_id, doc_type, skip, limit)


@router.get("/{user_id}/documents/{document_id}/download")
async def download_member_document(
    user_id: str,
    document_id: PydanticObjectId,
    _: CurrentUser = Depends(require_self_or_admin),
):
    return await _download(user_id, document_id)
