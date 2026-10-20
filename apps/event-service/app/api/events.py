from beanie import PydanticObjectId
from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    Query,
    Request,
    Response,
    UploadFile,
    status,
)
from pydantic import TypeAdapter, ValidationError

from app.api.deps import get_current_user, require_admin
from app.core.cache import cache_get, cache_set, get_list_version, invalidate_event
from app.core.config import settings
from app.core.limiter import limiter
from app.core.security import CurrentUser
from app.database.models import Event
from app.schemas.event import EventBase, EventCreate, EventResponse, EventUpdate
from app.utils.enums import EventCategory, EventStatus
from app.utils.helpers import utcnow
from app.utils.notifications import publish_notification
from app.utils.storage import delete_image, save_image

router = APIRouter(prefix="/events", tags=["Events"])

_event_adapter = TypeAdapter(EventResponse)
_events_adapter = TypeAdapter(list[EventResponse])


def _scope(user: CurrentUser) -> str:
    # Admins see drafts, others don't, so they must never share a cache entry.
    return "admin" if user.role == "admin" else "public"


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
    await invalidate_event()
    if event.status == EventStatus.PUBLISHED:
        await publish_notification({
            "event_id": f"event-service:{event.id}:published",
            "type": "event.published",
            "recipient_role": "user",
            "data": {"event_id": str(event.id), "screen": "event-details"},
        })
    return event


@router.patch("/{event_id}", response_model=EventResponse)
async def update_event(
    event_id: PydanticObjectId,
    payload: EventUpdate,
    _: CurrentUser = Depends(require_admin),
):
    event = await _get_or_404(event_id)
    was_published = event.status == EventStatus.PUBLISHED
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
    await invalidate_event(event.id)
    if event.status == EventStatus.PUBLISHED:
        event_type = "event.updated" if was_published else "event.published"
        await publish_notification({
            "event_id": f"event-service:{event.id}:{event_type.rsplit('.', 1)[1]}:{event.updated_at.isoformat()}",
            "type": event_type,
            "recipient_role": "user",
            "data": {"event_id": str(event.id), "screen": "event-details"},
        })
    return event


@router.delete("/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_event(event_id: PydanticObjectId, _: CurrentUser = Depends(require_admin)):
    event = await _get_or_404(event_id)
    for url in event.images:
        delete_image(url)
    await event.delete()
    await invalidate_event(event_id)


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
#     await invalidate_event(event.id)
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
#     await invalidate_event(event.id)
#     return event


# ---------- Any logged-in user: read (cached + rate-limited) ----------

@router.get("", response_model=list[EventResponse])
@limiter.limit(settings.RATE_LIMIT_READ)
async def list_events(
    request: Request,  # required by slowapi
    category: EventCategory | None = None,
    upcoming: bool | None = Query(None, description="true = future events only (soonest first)"),
    status_filter: EventStatus | None = Query(None, alias="status", description="Admin only"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    user: CurrentUser = Depends(get_current_user),
):
    version = await get_list_version()
    key = (
        f"events:list:v{version}:{_scope(user)}:"
        f"{category.value if category else '-'}:{upcoming}:"
        f"{status_filter.value if status_filter else '-'}:{skip}:{limit}"
    )
    if (cached := await cache_get(key)) is not None:
        return Response(cached, media_type="application/json")

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
    events = await Event.find(*conditions).sort(sort).skip(skip).limit(limit).to_list()

    body = _events_adapter.dump_json(
        _events_adapter.validate_python(events, from_attributes=True), by_alias=True
    )
    await cache_set(key, body, settings.CACHE_TTL_LIST)
    return Response(body, media_type="application/json")


@router.get("/{event_id}", response_model=EventResponse)
@limiter.limit(settings.RATE_LIMIT_READ)
async def get_event(
    request: Request,  # required by slowapi
    event_id: PydanticObjectId,
    user: CurrentUser = Depends(get_current_user),
):
    key = f"events:detail:{_scope(user)}:{event_id}"
    if (cached := await cache_get(key)) is not None:
        return Response(cached, media_type="application/json")

    event = await _get_or_404(event_id)
    if user.role != "admin" and event.status != EventStatus.PUBLISHED:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Event not found")

    body = _event_adapter.dump_json(
        _event_adapter.validate_python(event, from_attributes=True), by_alias=True
    )
    await cache_set(key, body, settings.CACHE_TTL_DETAIL)
    return Response(body, media_type="application/json")