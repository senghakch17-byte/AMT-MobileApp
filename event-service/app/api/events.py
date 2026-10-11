from beanie import PydanticObjectId
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from pydantic import ValidationError

from app.api.deps import get_current_user, require_admin
from app.core.config import settings
from app.core.security import CurrentUser
from app.database.models import Event
from app.schemas.event import EventBase, EventCreate, EventResponse, EventUpdate
from app.utils.enums import EventCategory, EventStatus
from app.utils.helpers import utcnow
from app.utils.storage import delete_image, save_image

router = APIRouter(prefix="/events", tags=["Events"])


async def _get_or_404(event_id: PydanticObjectId) -> Event:
    event = await Event.get(event_id)
    if event is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Event not found")
    return event


# ---------- Admin: create / update / delete ----------

@router.post("", response_model=EventResponse, status_code=status.HTTP_201_CREATED)
async def create_event(payload: EventCreate, admin: CurrentUser = Depends(require_admin)):
    event = Event(**payload.model_dump(), created_by=admin.id, created_by_email=admin.emailid)
    await event.insert()
    return event


@router.patch("/{event_id}", response_model=EventResponse)
async def update_event(
    event_id: PydanticObjectId,
    payload: EventUpdate,
    _: CurrentUser = Depends(require_admin),
):
    event = await _get_or_404(event_id)
    changes = payload.model_dump(exclude_unset=True)
    if not changes:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "No fields to update")
    try:  # re-validate merged result so cross-field rules (end_at >= start_at) still apply
        merged = EventBase.model_validate(
            {**event.model_dump(include=set(EventBase.model_fields)), **changes}
        )
    except ValidationError as exc:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            exc.errors(include_url=False, include_context=False, include_input=False),
        )
    for field in changes:
        setattr(event, field, getattr(merged, field))
    event.updated_at = utcnow()
    await event.save()
    return event


@router.delete("/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_event(event_id: PydanticObjectId, _: CurrentUser = Depends(require_admin)):
    event = await _get_or_404(event_id)
    for url in event.images:
        delete_image(url)
    await event.delete()


#================================================
# Under Development
#================================================
# ---------- Admin: photos ----------

# @router.post("/{event_id}/images", response_model=EventResponse)
# async def upload_event_images(
#     event_id: PydanticObjectId,
#     files: list[UploadFile] = File(...),
#     _: CurrentUser = Depends(require_admin),
# ):
#     event = await _get_or_404(event_id)
#     if len(event.images) + len(files) > settings.MAX_IMAGES_PER_EVENT:
#         raise HTTPException(
#             status.HTTP_400_BAD_REQUEST,
#             f"An event can have at most {settings.MAX_IMAGES_PER_EVENT} images",
#         )
#     saved: list[str] = []
#     try:
#         for f in files:
#             saved.append(await save_image(f))
#     except HTTPException:
#         for url in saved:  # roll back files from this batch
#             delete_image(url)
#         raise
#     event.images.extend(saved)
#     event.updated_at = utcnow()
#     await event.save()
#     return event


# @router.delete("/{event_id}/images", response_model=EventResponse)
# async def remove_event_image(
#     event_id: PydanticObjectId,
#     url: str = Query(..., description="Exact image URL from the event's images list"),
#     _: CurrentUser = Depends(require_admin),
# ):
#     event = await _get_or_404(event_id)
#     if url not in event.images:
#         raise HTTPException(status.HTTP_404_NOT_FOUND, "Image not found on this event")
#     event.images.remove(url)
#     delete_image(url)
#     event.updated_at = utcnow()
#     await event.save()
#     return event


# ---------- Any logged-in user: read ----------

@router.get("", response_model=list[EventResponse])
async def list_events(
    category: EventCategory | None = None,
    upcoming: bool | None = Query(None, description="true = future events only (soonest first)"),
    status_filter: EventStatus | None = Query(None, alias="status", description="Admin only"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    user: CurrentUser = Depends(get_current_user),
):
    conditions = []
    if user.role == "admin":
        if status_filter:
            conditions.append(Event.status == status_filter)
    else:
        conditions.append(Event.status == EventStatus.PUBLISHED)
    if category:
        conditions.append(Event.category == category)
    if upcoming:
        conditions.append(Event.start_at >= utcnow())
    sort = "+start_at" if upcoming else "-start_at"
    return await Event.find(*conditions).sort(sort).skip(skip).limit(limit).to_list()


@router.get("/{event_id}", response_model=EventResponse)
async def get_event(event_id: PydanticObjectId, user: CurrentUser = Depends(get_current_user)):
    event = await _get_or_404(event_id)
    if user.role != "admin" and event.status != EventStatus.PUBLISHED:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Event not found")
    return event