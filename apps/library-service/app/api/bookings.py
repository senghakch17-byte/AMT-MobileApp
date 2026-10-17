from datetime import datetime, timedelta

from beanie import PydanticObjectId
from beanie.operators import NE, In
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status

from app.api.deps import get_current_user, require_admin
from app.core.config import settings
from app.core.security import CurrentUser
from app.database.models import Booking, Room
from app.schemas.booking import BookingCreate, BookingDecision, BookingResponse
from app.utils.enums import BookingStatus
from app.utils.helpers import to_utc, utcnow

router = APIRouter(prefix="/bookings", tags=["Bookings"])

ACTIVE = [BookingStatus.PENDING, BookingStatus.APPROVED]


def _invalid(message: str) -> HTTPException:
    return HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, message)


def _conflict(message: str) -> HTTPException:
    return HTTPException(status.HTTP_409_CONFLICT, message)


async def _get_or_404(booking_id: PydanticObjectId, user: CurrentUser) -> Booking:
    booking = await Booking.get(booking_id)
    # a user can't tell whether someone else's booking exists
    if booking is None or (user.role != "admin" and booking.user_id != user.id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Booking not found")
    return booking


async def _room_taken(room_id: PydanticObjectId, start: datetime, end: datetime, exclude=None) -> bool:
    """True if an approved booking overlaps [start, end). Only approved bookings hold a room."""
    conditions = [
        Booking.room_id == room_id,
        Booking.status == BookingStatus.APPROVED,
        Booking.start_at < end,
        Booking.end_at > start,
    ]
    if exclude is not None:
        conditions.append(NE(Booking.id, exclude))
    return await Booking.find(*conditions).count() > 0


async def _approve(booking: Booking, decided_by: str, note: str | None = None) -> None:
    """Move a pending booking to approved, guaranteeing the room is never double-booked.

    Mongo can't enforce "no overlapping ranges" with an index, so: check, write, then check
    again. If a concurrent request got in between, this one backs out (worst case both do,
    and the users retry) rather than ever leaving two approved bookings in one slot.
    """
    if await _room_taken(booking.room_id, booking.start_at, booking.end_at, exclude=booking.id):
        raise _conflict("The room is already booked for that time")
    now = utcnow()
    booking.status = BookingStatus.APPROVED
    booking.decided_by, booking.decided_at, booking.admin_note = decided_by, now, note
    booking.updated_at = now
    await booking.save()
    if await _room_taken(booking.room_id, booking.start_at, booking.end_at, exclude=booking.id):
        booking.status = BookingStatus.PENDING
        booking.decided_by = booking.decided_at = booking.admin_note = None
        booking.updated_at = utcnow()
        await booking.save()
        raise _conflict("The room was just booked by someone else")


# ---------- User: make a booking ----------

@router.post("", response_model=BookingResponse, status_code=status.HTTP_201_CREATED)
async def create_booking(payload: BookingCreate, user: CurrentUser = Depends(get_current_user)):
    # cheap checks that need no database first
    if payload.start_at <= utcnow():
        raise _invalid("start_at must be in the future")
    length = payload.end_at - payload.start_at
    if length < timedelta(minutes=settings.MIN_BOOKING_MINUTES):
        raise _invalid(f"A booking must be at least {settings.MIN_BOOKING_MINUTES} minutes")
    if length > timedelta(hours=settings.MAX_BOOKING_HOURS):
        raise _invalid(f"A booking can be at most {settings.MAX_BOOKING_HOURS} hours")

    room = await Room.get(payload.room_id)
    if room is None or not room.is_active:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Room not found")
    if payload.attendees > room.capacity:
        raise _invalid(f"Room capacity is {room.capacity}")

    if await _room_taken(room.id, payload.start_at, payload.end_at):
        raise _conflict("The room is already booked for that time")
    if await Booking.find(
        Booking.user_id == user.id,
        In(Booking.status, ACTIVE),
        Booking.start_at < payload.end_at,
        Booking.end_at > payload.start_at,
    ).count():
        raise _conflict("You already have a booking that overlaps this time")

    booking = Booking(
        room_id=room.id,
        room_name=room.name,
        user_id=user.id,
        user_email=user.emailid,
        start_at=payload.start_at,
        end_at=payload.end_at,
        attendees=payload.attendees,
        purpose=payload.purpose.strip(),
    )
    await booking.insert()
    if not settings.REQUIRE_BOOKING_APPROVAL:
        try:
            await _approve(booking, decided_by="system")
        except HTTPException:
            await booking.delete()  # the user never got a booking, so leave no trace
            raise
    return booking


# ---------- User: own bookings ----------
# NOTE: "/me" is declared before "/{booking_id}" so "me" is never read as an id.

@router.get("/me", response_model=list[BookingResponse])
async def list_my_bookings(
    response: Response,
    status_filter: BookingStatus | None = Query(None, alias="status"),
    upcoming: bool | None = Query(None, description="true = bookings that have not ended yet"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    user: CurrentUser = Depends(get_current_user),
):
    conditions = [Booking.user_id == user.id]
    if status_filter:
        conditions.append(Booking.status == status_filter)
    if upcoming:
        conditions.append(Booking.end_at >= utcnow())
    query = Booking.find(*conditions)
    response.headers["X-Total-Count"] = str(await query.count())
    return await query.sort("-start_at").skip(skip).limit(limit).to_list()


# ---------- Admin: booking history ----------

@router.get("", response_model=list[BookingResponse])
async def list_all_bookings(
    response: Response,
    status_filter: BookingStatus | None = Query(None, alias="status", description="pending = approval queue"),
    room_id: PydanticObjectId | None = None,
    user_id: str | None = None,
    start_from: datetime | None = Query(None, description="Bookings starting at or after this"),
    start_to: datetime | None = Query(None, description="Bookings starting before this"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    _: CurrentUser = Depends(require_admin),
):
    conditions = []
    if status_filter:
        conditions.append(Booking.status == status_filter)
    if room_id:
        conditions.append(Booking.room_id == room_id)
    if user_id:
        conditions.append(Booking.user_id == user_id)
    if start_from:
        conditions.append(Booking.start_at >= to_utc(start_from))
    if start_to:
        conditions.append(Booking.start_at < to_utc(start_to))
    query = Booking.find(*conditions)
    response.headers["X-Total-Count"] = str(await query.count())
    return await query.sort("-start_at").skip(skip).limit(limit).to_list()


# ---------- Owner or admin ----------

@router.get("/{booking_id}", response_model=BookingResponse)
async def get_booking(booking_id: PydanticObjectId, user: CurrentUser = Depends(get_current_user)):
    return await _get_or_404(booking_id, user)


@router.post("/{booking_id}/cancel", response_model=BookingResponse)
async def cancel_booking(booking_id: PydanticObjectId, user: CurrentUser = Depends(get_current_user)):
    booking = await _get_or_404(booking_id, user)
    if booking.status not in ACTIVE:
        raise _conflict(f"A {booking.status.value} booking cannot be cancelled")
    if booking.start_at <= utcnow():
        raise _conflict("A booking that has already started cannot be cancelled")
    booking.status = BookingStatus.CANCELLED
    if booking.user_id != user.id:  # an admin cancelled someone else's booking
        booking.decided_by, booking.decided_at = user.id, utcnow()
    booking.updated_at = utcnow()
    await booking.save()
    return booking


# ---------- Admin: approve / reject ----------

@router.post("/{booking_id}/approve", response_model=BookingResponse)
async def approve_booking(
    booking_id: PydanticObjectId,
    payload: BookingDecision | None = None,
    admin: CurrentUser = Depends(require_admin),
):
    booking = await _get_or_404(booking_id, admin)
    if booking.status != BookingStatus.PENDING:
        raise _conflict(f"Only pending bookings can be approved (this one is {booking.status.value})")
    if booking.start_at <= utcnow():
        raise _conflict("This booking's start time has already passed")
    room = await Room.get(booking.room_id)
    if room is None or not room.is_active:
        raise _conflict("This room is no longer available for booking")
    await _approve(booking, decided_by=admin.id, note=payload.note if payload else None)
    return booking


@router.post("/{booking_id}/reject", response_model=BookingResponse)
async def reject_booking(
    booking_id: PydanticObjectId,
    payload: BookingDecision | None = None,
    admin: CurrentUser = Depends(require_admin),
):
    booking = await _get_or_404(booking_id, admin)
    if booking.status != BookingStatus.PENDING:
        raise _conflict(f"Only pending bookings can be rejected (this one is {booking.status.value})")
    now = utcnow()
    booking.status = BookingStatus.REJECTED
    booking.decided_by, booking.decided_at = admin.id, now
    booking.admin_note = payload.note if payload else None
    booking.updated_at = now
    await booking.save()
    return booking
