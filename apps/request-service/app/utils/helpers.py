from datetime import datetime, timezone

from beanie import Document, PydanticObjectId
from fastapi import HTTPException, status
from pydantic import BaseModel, ValidationError

from app.core.security import CurrentUser
from app.utils.enums import RequestStatus


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


async def get_owned_or_404(
    model: type[Document], request_id: PydanticObjectId, user: CurrentUser
):
    doc = await model.get(request_id)
    # 404 (not 403) so users can't probe for other people's request IDs
    if doc is None or doc.student_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Request not found")
    return doc


def ensure_pending(doc) -> None:
    if doc.status != RequestStatus.PENDING:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            f"Request is already {doc.status.value}; only pending requests can be changed",
        )


def apply_update(doc, schema: type[BaseModel], payload: BaseModel) -> None:
    """Merge partial changes into doc (in memory) and re-run the full create-schema validation."""
    changes = payload.model_dump(exclude_unset=True)
    if not changes:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "No fields to update")
    try:
        merged = schema.model_validate({**doc.model_dump(), **changes})
    except ValidationError as exc:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            exc.errors(include_url=False, include_context=False, include_input=False),
        )
    for field in changes:
        setattr(doc, field, getattr(merged, field))
    doc.updated_at = utcnow()


def mark_cancelled(doc) -> None:
    doc.status = RequestStatus.CANCELLED
    doc.cancelled_at = doc.updated_at = utcnow()