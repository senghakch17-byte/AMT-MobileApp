from beanie import PydanticObjectId
from beanie.operators import In
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status

from app.api.deps import get_current_user
from app.core.cache import bump_version, cached_list
from app.core.limiter import limiter
from app.core.security import CurrentUser
from app.database.models import PreScholarshipRegistration as Registration
from app.schemas.pre_scholarship import (
    PreScholarshipBase,
    PreScholarshipResponse,
    PreScholarshipUpdate,
)
from app.utils.enums import RequestStatus
from app.utils.helpers import (
    apply_update,
    ensure_pending,
    get_owned_or_404,
    mark_cancelled,
)

router = APIRouter(
    prefix="/pre-scholarship-registrations",
    tags=["Pre-Scholarship Registration"],
)

ACTIVE = [RequestStatus.PENDING.value, RequestStatus.APPROVED.value]
NS = "prescholarship"


async def _ensure_not_duplicate(
    student_id: str, academic_year: str, exclude_id=None
) -> None:
    conditions = [
        Registration.student_id == student_id,
        Registration.academic_year == academic_year,
        In(Registration.status, ACTIVE),
    ]
    if exclude_id:
        conditions.append(Registration.id != exclude_id)
    if await Registration.find_one(*conditions):
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            f"You already have an active registration for {academic_year}",
        )


@router.post(
    "",
    response_model=PreScholarshipResponse,
    status_code=status.HTTP_201_CREATED,
)
async def send_registration(
    payload: PreScholarshipBase, user: CurrentUser = Depends(get_current_user)
):
    await _ensure_not_duplicate(user.id, payload.academic_year)
    doc = Registration(
        **payload.model_dump(), student_id=user.id, student_email=user.emailid
    )
    await doc.insert()
    await bump_version(NS, user.id)
    return doc


@router.get("", response_model=list[PreScholarshipResponse])
@limiter.limit("60/minute")
async def list_my_registrations(
    request: Request,
    status_filter: RequestStatus | None = Query(None, alias="status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    user: CurrentUser = Depends(get_current_user),
):
    async def load():
        query = Registration.find(Registration.student_id == user.id)
        if status_filter:
            query = query.find(Registration.status == status_filter)
        docs = await query.sort("-created_at").skip(skip).limit(limit).to_list()
        return [
            PreScholarshipResponse.model_validate(d, from_attributes=True).model_dump(mode="json")
            for d in docs
        ]

    sub = f"{status_filter.value if status_filter else 'all'}:{skip}:{limit}"
    return await cached_list(NS, user.id, sub, load)


#===============================================
# Under Development
#===============================================
# @router.get("/{request_id}", response_model=PreScholarshipResponse)
# async def get_registration(
#     request_id: PydanticObjectId, user: CurrentUser = Depends(get_current_user)
# ):
#     return await get_owned_or_404(Registration, request_id, user)


# @router.patch("/{request_id}", response_model=PreScholarshipResponse)
# async def update_registration(
#     request_id: PydanticObjectId,
#     payload: PreScholarshipUpdate,
#     user: CurrentUser = Depends(get_current_user),
# ):
#     doc = await get_owned_or_404(Registration, request_id, user)
#     ensure_pending(doc)
#     apply_update(doc, PreScholarshipBase, payload)
#     await _ensure_not_duplicate(user.id, doc.academic_year, exclude_id=doc.id)
#     await doc.save()
#     return doc


# @router.patch("/{request_id}/cancel", response_model=PreScholarshipResponse)
# async def cancel_registration(
#     request_id: PydanticObjectId, user: CurrentUser = Depends(get_current_user)
# ):
#     doc = await get_owned_or_404(Registration, request_id, user)
#     ensure_pending(doc)
#     mark_cancelled(doc)
#     await doc.save()
#     return doc