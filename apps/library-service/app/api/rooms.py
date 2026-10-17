import re
from datetime import datetime, timedelta

from beanie import PydanticObjectId
from beanie.operators import Or, RegEx
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from pymongo.errors import DuplicateKeyError

from app.api.deps import get_current_user, require_admin
from app.core.security import CurrentUser
from app.database.models import Booking, Room
from app.schemas.room import BusySlot, RoomBase, RoomCreate, RoomResponse, RoomUpdate
from app.utils.enums import BookingStatus
from app.utils.helpers import apply_update, to_utc

router = APIRouter(prefix="/rooms", tags=["Rooms"])

MAX_AVAILABILITY_DAYS = 31


async def _get_or_404(room_id: PydanticObjectId, user: CurrentUser | None = None) -> Room:
    room = await Room.get(room_id)
    # inactive rooms are invisible to everyone except admins
    if room is None or (not room.is_active and (user is None or user.role != "admin")):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Room not found")
    return room


def _name_taken() -> HTTPException:
    return HTTPException(status.HTTP_409_CONFLICT, "A room with this name already exists")


# ---------- Admin: room information ----------

@router.post("", response_model=RoomResponse, status_code=status.HTTP_201_CREATED)
async def create_room(payload: RoomCreate, admin: CurrentUser = Depends(require_admin)):
    room = Room(**payload.model_dump(), created_by=admin.id)
    try:
        await room.insert()
    except DuplicateKeyError:
        raise _name_taken()
    return room


@router.patch("/{room_id}", response_model=RoomResponse)
async def update_room(
    room_id: PydanticObjectId, payload: RoomUpdate, user: CurrentUser = Depends(require_admin)
):
    if not payload.model_fields_set:  # nothing to change: no need to touch the database
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "No fields to update")
    room = await _get_or_404(room_id, user)
    apply_update(room, RoomBase, payload)
    try:
        await room.save()
    except DuplicateKeyError:
        raise _name_taken()
    return room


@router.delete("/{room_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_room(room_id: PydanticObjectId, user: CurrentUser = Depends(require_admin)):
    room = await _get_or_404(room_id, user)
    if await Booking.find(Booking.room_id == room.id).count():
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "Room has booking history and cannot be deleted; set is_active to false instead",
        )
    await room.delete()


# ---------- Any logged-in user: read ----------

@router.get("", response_model=list[RoomResponse])
async def list_rooms(
    response: Response,
    q: str | None = Query(None, min_length=1, max_length=100, description="Search name or location"),
    min_capacity: int | None = Query(None, ge=1),
    amenity: str | None = Query(None, min_length=1, max_length=50),
    is_active: bool | None = Query(None, description="Admin only"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    user: CurrentUser = Depends(get_current_user),
):
    conditions = []
    if user.role == "admin":
        if is_active is not None:
            conditions.append(Room.is_active == is_active)
    else:
        conditions.append(Room.is_active == True)  # noqa: E712 (Beanie needs ==)
    if q:
        pattern = re.escape(q)  # user input is matched literally, never as a regex
        conditions.append(
            Or(RegEx(Room.name, pattern, "i"), RegEx(Room.location, pattern, "i"))
        )
    if min_capacity:
        conditions.append(Room.capacity >= min_capacity)
    if amenity:
        conditions.append(RegEx(Room.amenities, f"^{re.escape(amenity)}$", "i"))
    query = Room.find(*conditions)
    response.headers["X-Total-Count"] = str(await query.count())
    return await query.sort("+name").skip(skip).limit(limit).to_list()


@router.get("/{room_id}", response_model=RoomResponse)
async def get_room(room_id: PydanticObjectId, user: CurrentUser = Depends(get_current_user)):
    return await _get_or_404(room_id, user)


@router.get("/{room_id}/availability", response_model=list[BusySlot])
async def room_availability(
    room_id: PydanticObjectId,
    start: datetime = Query(..., description="Window start"),
    end: datetime = Query(..., description="Window end (at most 31 days after start)"),
    user: CurrentUser = Depends(get_current_user),
):
    """Approved bookings in the window, so a user can pick a free slot."""
    start, end = to_utc(start), to_utc(end)
    if end <= start:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "end must be after start")
    if end - start > timedelta(days=MAX_AVAILABILITY_DAYS):
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            f"window can be at most {MAX_AVAILABILITY_DAYS} days",
        )
    room = await _get_or_404(room_id, user)
    booked = await (
        Booking.find(
            Booking.room_id == room.id,
            Booking.status == BookingStatus.APPROVED,
            Booking.start_at < end,
            Booking.end_at > start,
        )
        .sort("+start_at")
        .to_list()
    )
    return [BusySlot(start_at=b.start_at, end_at=b.end_at) for b in booked]
