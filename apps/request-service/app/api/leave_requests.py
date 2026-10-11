from datetime import date

from beanie import PydanticObjectId
from beanie.operators import In
from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.deps import get_current_user
from app.core.security import CurrentUser
from app.database.models import LeaveRequest
from app.schemas.leave_request import (
    LeaveRequestBase,
    LeaveRequestResponse,
    LeaveRequestUpdate,
)
from app.utils.enums import RequestStatus
from app.utils.helpers import (
    apply_update,
    ensure_pending,
    get_owned_or_404,
    mark_cancelled,
)

router = APIRouter(prefix="/leave-requests", tags=["Leave Requests"])

ACTIVE = [RequestStatus.PENDING.value, RequestStatus.APPROVED.value]


async def _ensure_no_overlap(
    student_id: str, start: date, end: date, exclude_id=None
) -> None:
    conditions = [
        LeaveRequest.student_id == student_id,
        In(LeaveRequest.status, ACTIVE),
        LeaveRequest.start_date <= end,
        LeaveRequest.end_date >= start,
    ]
    if exclude_id:
        conditions.append(LeaveRequest.id != exclude_id)
    if await LeaveRequest.find_one(*conditions):
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "You already have a pending/approved leave request overlapping these dates",
        )


@router.post(
    "", response_model=LeaveRequestResponse, status_code=status.HTTP_201_CREATED
)
async def send_leave_request(
    payload: LeaveRequestBase, user: CurrentUser = Depends(get_current_user)
):
    await _ensure_no_overlap(user.id, payload.start_date, payload.end_date)
    doc = LeaveRequest(
        **payload.model_dump(), student_id=user.id, student_email=user.emailid
    )
    await doc.insert()
    return doc


@router.get("", response_model=list[LeaveRequestResponse])
async def list_my_leave_requests(
    status_filter: RequestStatus | None = Query(None, alias="status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    user: CurrentUser = Depends(get_current_user),
):
    query = LeaveRequest.find(LeaveRequest.student_id == user.id)
    if status_filter:
        query = query.find(LeaveRequest.status == status_filter)
    return await query.sort("-created_at").skip(skip).limit(limit).to_list()


@router.get("/{request_id}", response_model=LeaveRequestResponse)
async def get_leave_request(
    request_id: PydanticObjectId, user: CurrentUser = Depends(get_current_user)
):
    return await get_owned_or_404(LeaveRequest, request_id, user)


@router.patch("/{request_id}", response_model=LeaveRequestResponse)
async def update_leave_request(
    request_id: PydanticObjectId,
    payload: LeaveRequestUpdate,
    user: CurrentUser = Depends(get_current_user),
):
    doc = await get_owned_or_404(LeaveRequest, request_id, user)
    ensure_pending(doc)
    apply_update(doc, LeaveRequestBase, payload)
    await _ensure_no_overlap(
        user.id, doc.start_date, doc.end_date, exclude_id=doc.id
    )
    await doc.save()
    return doc


@router.patch("/{request_id}/cancel", response_model=LeaveRequestResponse)
async def cancel_leave_request(
    request_id: PydanticObjectId, user: CurrentUser = Depends(get_current_user)
):
    doc = await get_owned_or_404(LeaveRequest, request_id, user)
    ensure_pending(doc)
    mark_cancelled(doc)
    await doc.save()
    return doc