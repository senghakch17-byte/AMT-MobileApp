from beanie import PydanticObjectId
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    Request,
    Response,
    status,
)
from pydantic import TypeAdapter, ValidationError

from app.api.deps import get_current_user, require_admin
from app.core.cache import cache_get, cache_set, get_list_version, invalidate_announcement
from app.core.config import settings
from app.core.limiter import limiter
from app.core.security import CurrentUser
from app.database.models import Announcement
from app.schemas.announcement import AnnouncementBase, AnnouncementCreate, AnnouncementResponse, AnnouncementUpdate
from app.utils.enums import AnnouncementCategory, AnnouncementStatus
from app.utils.helpers import utcnow
from app.utils.notifications import publish_notification
from app.utils.storage import delete_image

router = APIRouter(tags=["Announcements"])

_announcement_adapter = TypeAdapter(AnnouncementResponse)
_announcements_adapter = TypeAdapter(list[AnnouncementResponse])


def _scope(user: CurrentUser) -> str:
    # Admins see drafts, others don't, so they must never share a cache entry.
    return "admin" if user.role == "admin" else "public"


async def _get_or_404(announcement_id: PydanticObjectId) -> Announcement:
    announcement = await Announcement.get(announcement_id)
    if announcement is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Announcement not found")
    return announcement


# ---------- Admin: create / update / delete ----------

@router.post("/", response_model=AnnouncementResponse, status_code=status.HTTP_201_CREATED)
async def create_announcement(payload: AnnouncementCreate, admin: CurrentUser = Depends(require_admin)):
    announcement = Announcement(**payload.model_dump(), created_by=admin.id, created_by_email=admin.emailid)
    await announcement.insert()
    await invalidate_announcement()
    if announcement.status == AnnouncementStatus.PUBLISHED:
        await publish_notification({
            "notification_key": f"announcement-service:{announcement.id}:published",
            "type": "announcement.published",
            "recipient_role": "user",
            "data": {"announcement_id": str(announcement.id), "screen": "announcement-details"},
        })
    return announcement


@router.patch("/{announcement_id}", response_model=AnnouncementResponse)
async def update_announcement(
    announcement_id: PydanticObjectId,
    payload: AnnouncementUpdate,
    _: CurrentUser = Depends(require_admin),
):
    announcement = await _get_or_404(announcement_id)
    was_published = announcement.status == AnnouncementStatus.PUBLISHED
    changes = payload.model_dump(exclude_unset=True)
    if not changes:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "No fields to update")
    try:  # re-validate merged result so cross-field rules (end_at >= start_at) still apply
        merged = AnnouncementBase.model_validate(
            {**announcement.model_dump(include=set(AnnouncementBase.model_fields)), **changes}
        )
    except ValidationError as exc:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            exc.errors(include_url=False, include_context=False, include_input=False),
        )
    for field in changes:
        setattr(announcement, field, getattr(merged, field))
    announcement.updated_at = utcnow()
    await announcement.save()
    await invalidate_announcement(announcement.id)
    if announcement.status == AnnouncementStatus.PUBLISHED:
        notification_type = "announcement.updated" if was_published else "announcement.published"
        await publish_notification({
            "notification_key": f"announcement-service:{announcement.id}:{notification_type.rsplit('.', 1)[1]}:{announcement.updated_at.isoformat()}",
            "type": notification_type,
            "recipient_role": "user",
            "data": {"announcement_id": str(announcement.id), "screen": "announcement-details"},
        })
    return announcement


@router.delete("/{announcement_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_announcement(announcement_id: PydanticObjectId, _: CurrentUser = Depends(require_admin)):
    announcement = await _get_or_404(announcement_id)
    for url in announcement.images:
        delete_image(url)
    await announcement.delete()
    await invalidate_announcement(announcement_id)


# ---------- Any logged-in user: read (cached + rate-limited) ----------

@router.get("/", response_model=list[AnnouncementResponse])
@limiter.limit(settings.RATE_LIMIT_READ)
async def list_announcements(
    request: Request,  # required by slowapi
    category: AnnouncementCategory | None = None,
    upcoming: bool | None = Query(None, description="true = future announcements only (soonest first)"),
    status_filter: AnnouncementStatus | None = Query(None, alias="status", description="Admin only"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    user: CurrentUser = Depends(get_current_user),
):
    version = await get_list_version()
    key = (
        f"announcements:list:v{version}:{_scope(user)}:"
        f"{category.value if category else '-'}:{upcoming}:"
        f"{status_filter.value if status_filter else '-'}:{skip}:{limit}"
    )
    if (cached := await cache_get(key)) is not None:
        return Response(cached, media_type="application/json")

    conditions = []
    if user.role == "admin":
        if status_filter:
            conditions.append(Announcement.status == status_filter)
    else:
        conditions.append(Announcement.status == AnnouncementStatus.PUBLISHED)
    if category:
        conditions.append(Announcement.category == category)
    if upcoming:
        conditions.append(Announcement.start_at >= utcnow())
    sort = "+start_at" if upcoming else "-start_at"
    announcements = await Announcement.find(*conditions).sort(sort).skip(skip).limit(limit).to_list()

    body = _announcements_adapter.dump_json(
        _announcements_adapter.validate_python(announcements, from_attributes=True), by_alias=True
    )
    await cache_set(key, body, settings.CACHE_TTL_LIST)
    return Response(body, media_type="application/json")


@router.get("/all", response_model=list[AnnouncementResponse])
async def list_all_announcements(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    _: CurrentUser = Depends(require_admin),
):
    """Administrative view that always includes drafts and published announcements."""
    return await Announcement.find().sort("-created_at").skip(skip).limit(limit).to_list()


@router.get("/{announcement_id}", response_model=AnnouncementResponse)
@limiter.limit(settings.RATE_LIMIT_READ)
async def get_announcement(
    request: Request,  # required by slowapi
    announcement_id: PydanticObjectId,
    user: CurrentUser = Depends(get_current_user),
):
    key = f"announcements:detail:{_scope(user)}:{announcement_id}"
    if (cached := await cache_get(key)) is not None:
        return Response(cached, media_type="application/json")

    announcement = await _get_or_404(announcement_id)
    if user.role != "admin" and announcement.status != AnnouncementStatus.PUBLISHED:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Announcement not found")

    body = _announcement_adapter.dump_json(
        _announcement_adapter.validate_python(announcement, from_attributes=True), by_alias=True
    )
    await cache_set(key, body, settings.CACHE_TTL_DETAIL)
    return Response(body, media_type="application/json")
