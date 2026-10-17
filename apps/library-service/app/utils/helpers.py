from datetime import datetime, timezone

from fastapi import HTTPException, status
from pydantic import ValidationError


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def to_utc(value: datetime | None) -> datetime | None:
    """Naive datetimes are treated as UTC; aware ones are converted to UTC."""
    if value is None:
        return None
    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value.astimezone(timezone.utc)


def apply_update(doc, base_cls, payload) -> None:
    """Apply a partial update to a document.

    The merged result is re-validated against `base_cls` so field rules (and any
    cross-field rules) still hold, and `updated_at` is bumped. Raises 400 when the
    payload is empty and 422 when the merged result is invalid.
    """
    changes = payload.model_dump(exclude_unset=True)
    if not changes:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "No fields to update")
    try:
        merged = base_cls.model_validate(
            {**doc.model_dump(include=set(base_cls.model_fields)), **changes}
        )
    except ValidationError as exc:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            exc.errors(include_url=False, include_context=False, include_input=False),
        )
    for field in changes:
        setattr(doc, field, getattr(merged, field))
    doc.updated_at = utcnow()
